import os
import csv
import re
from typing import Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from regulacao.models import TipoExame


def _norm(s: str) -> str:
    return (s or '').strip().upper()


def _find_table_file(root: str, base_name: str) -> Optional[str]:
    """Search recursively for files like tb_procedimento*.csv/.txt (case-insensitive)."""
    target_lower = base_name.lower()
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            low = name.lower()
            if low.startswith(target_lower) and (low.endswith('.csv') or low.endswith('.txt')):
                return os.path.join(dirpath, name)
    return None


def _read_table_flexible(path: str, encoding: str = 'latin-1') -> Tuple[List[str], List[List[str]]]:
    """Read CSV/TXT trying common SIGTAP delimiters and detect header if present.
    Returns (header, rows). If header is not detected, returns empty header and all rows as data.
    """
    delimiters = [';', ',', '\t', '|']
    encodings = []
    for e in [encoding, 'utf-8', 'utf-8-sig', 'latin-1']:
        if e and e not in encodings:
            encodings.append(e)
    for enc_try in encodings:
        for delim in delimiters:
            try:
                with open(path, 'r', encoding=enc_try, newline='') as f:
                    reader = csv.reader(f, delimiter=delim)
                    rows = []
                    for r in reader:
                        # Skip empty/whitespace-only rows
                        if not r or all((c or '').strip() == '' for c in r):
                            continue
                        rows.append([ (c or '').strip() for c in r ])
            except Exception:
                continue
            if not rows:
                continue
            # Fixed-width fallback: when lines are single-field and start with 10-digit code
            if rows and sum(1 for r in rows if len(r) == 1) >= int(0.8 * len(rows)):
                rows_fixed: List[List[str]] = []
                for r in rows:
                    s = (r[0] or '').strip()
                    m = re.match(r'^(\d{10})(.*)$', s)
                    if not m:
                        continue
                    cod = m.group(1)
                    rest = (m.group(2) or '').strip()
                    # Nome: parte inicial não numérica
                    mname = re.match(r'^([^\d]+)', rest)
                    nome = (mname.group(1) if mname else rest).strip()
                    rows_fixed.append([cod, nome])
                if rows_fixed:
                    return [], rows_fixed
            # Heuristic: header if it contains known column tokens or non-numeric in many columns
            first = [c.strip() for c in rows[0]]
            upper = [c.upper() for c in first]
            header_tokens = {'CO_PROCEDIMENTO', 'NO_PROCEDIMENTO', 'CO_GRUPO', 'CO_COMPETENCIA', 'DT_COMPETENCIA'}
            has_known = any(u in header_tokens or u.startswith('CO_') or u.startswith('NO_') for u in upper)
            if has_known:
                return first, rows[1:]
            # If first row looks like codes (mostly numeric), treat as data (no header)
            return [], rows
    # Fallback: empty
    return [], []


def _parse_valor_line_fallback(s: str) -> Optional[Tuple[str, str, float]]:
    """Heurística para extrair (codigo, competencia, valor_total) de uma linha sem delimitadores.
    - codigo: primeiros 10 dígitos
    - competencia: primeira ocorrência AAAAMM (19|20)\d{4}
    - valor_total: soma de até 3 valores monetários detectados; tenta com decimais (\d+[\.,]\d{2});
      se não houver, tenta 3 grupos numéricos grandes no final como centavos.
    """
    if not s:
        return None
    m = re.match(r'^(\d{10})(.*)$', s.strip())
    if not m:
        return None
    cod = m.group(1)
    rest = m.group(2)
    # competência
    mcomp = re.search(r'(19|20)\d{4}', rest)
    comp = mcomp.group(0) if mcomp else ''
    # valores com decimais
    decs = re.findall(r'(\d+[\.,]\d{2})', rest)
    vals: List[float] = []
    for d in decs[-3:]:
        try:
            vals.append(float(d.replace('.', '').replace(',', '.')))
        except Exception:
            continue
    if not vals:
        # tentar grupos numéricos longos como centavos; pegar últimos 3
        nums = re.findall(r'(\d{5,})', rest)
        cents = []
        for n in nums[-3:]:
            try:
                cents.append(int(n) / 100.0)
            except Exception:
                continue
        vals = cents
    total = sum(vals) if vals else 0.0
    return cod, comp, total


def _detect_columns(header: List[str], rows: List[List[str]]) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """Return (i_cod, i_nome, i_grupo) using header names or heuristics.
    i_cod: column with 10-digit numeric code; i_nome: text/name; i_grupo: 2-digit group if found.
    """
    def norm(s: str) -> str:
        return (s or '').strip().upper()

    i_cod = i_nome = i_grup = None
    head_map: Dict[str, int] = {}
    if header:
        head_map = { norm(h): idx for idx, h in enumerate(header) }
        # Direct and prefix matches
        def idx_for(*cands: str) -> Optional[int]:
            for cand in cands:
                key = norm(cand)
                if key in head_map:
                    return head_map[key]
            # startswith matches
            for cand in cands:
                key = norm(cand)
                for h, i in head_map.items():
                    if h.startswith(key):
                        return i
            return None
        i_cod = idx_for('CO_PROCEDIMENTO', 'CO_PROCED', 'CO_PROC', 'COD_PROCEDIMENTO')
        i_nome = idx_for('NO_PROCEDIMENTO', 'NO_PROCED', 'NOME_PROCEDIMENTO', 'DS_PROCEDIMENTO')
        i_grup = idx_for('CO_GRUPO', 'CO_GRUP', 'GRUPO')

    # Heuristic if missing
    sample = rows[:200]
    if i_cod is None and sample:
        # Choose column with most 10-digit numeric strings
        counts: Dict[int, int] = {}
        for r in sample:
            for idx, val in enumerate(r):
                if re.fullmatch(r"\d{10}", (val or '').strip()):
                    counts[idx] = counts.get(idx, 0) + 1
        if counts:
            i_cod = max(counts.items(), key=lambda x: x[1])[0]

    if i_nome is None and sample:
        # Choose the column with highest average length containing alphabetic chars, excluding i_cod
        metrics: Dict[int, Tuple[int, int]] = {}  # idx -> (total_len, count)
        for r in sample:
            for idx, val in enumerate(r):
                if idx == i_cod:
                    continue
                s = (val or '').strip()
                if any(ch.isalpha() for ch in s) and len(s) >= 3:
                    total, cnt = metrics.get(idx, (0, 0))
                    metrics[idx] = (total + len(s), cnt + 1)
        if metrics:
            i_nome = max(metrics.items(), key=lambda x: (x[1][0] / max(1, x[1][1])))[0]

    if i_grup is None and sample:
        # Prefer column with many 2-digit numeric codes (e.g., '04')
        counts2: Dict[int, int] = {}
        for r in sample:
            for idx, val in enumerate(r):
                if re.fullmatch(r"\d{2}", (val or '').strip()):
                    counts2[idx] = counts2.get(idx, 0) + 1
        if counts2:
            i_grup = max(counts2.items(), key=lambda x: x[1])[0]

    return i_cod, i_nome, i_grup


class Command(BaseCommand):
    help = (
        "Importa procedimentos do SIGTAP para TipoExame.\n"
        "Uso: python manage.py import_sigtap_exames --path <pasta extraída SIGTAP> [--only-groups 04,05] [--name-contains EXAME,LAB] [--set-valor] [--encoding latin-1]"
    )

    def add_arguments(self, parser):
        parser.add_argument('--path', required=True, help='Caminho da pasta com arquivos SIGTAP extraídos (tb_procedimento, tb_procedimento_valor etc).')
        parser.add_argument('--only-groups', default='', help='Importar apenas procedimentos com CO_GRUPO em uma lista separada por vírgulas (ex: 04,05).')
        parser.add_argument('--name-contains', default='', help='Importar apenas se NO_PROCEDIMENTO contém qualquer um dos termos (separar por vírgula).')
        parser.add_argument('--set-valor', action='store_true', help='Se presente, tenta importar valores (VL_SH + VL_SA + VL_SP) da tabela tb_procedimento_valor, escolhendo a última competência.')
        parser.add_argument('--encoding', default='latin-1', help='Encoding dos arquivos (padrão latin-1).')

    def handle(self, *args, **opts):
        root = opts['path']
        if not os.path.exists(root):
            raise CommandError(f"Caminho não encontrado: {root}")
        if os.path.isfile(root):
            # Se for um RAR, orientar a extrair
            low = root.lower()
            if low.endswith('.rar'):
                raise CommandError('Forneça o caminho de uma PASTA com os arquivos SIGTAP extraídos (o .rar deve ser extraído antes).')
            else:
                raise CommandError('Forneça o caminho de uma pasta contendo os arquivos do SIGTAP (tb_procedimento*.csv/txt).')

        enc = opts['encoding']
        only_groups = [_norm(x) for x in (opts['only_groups'].split(',') if opts['only_groups'] else []) if x.strip()]
        name_terms = [_norm(x) for x in (opts['name_contains'].split(',') if opts['name_contains'] else []) if x.strip()]
        set_valor = bool(opts['set_valor'])

        # Localizar arquivos
        proc_path = _find_table_file(root, 'tb_procedimento')
        if not proc_path:
            raise CommandError('Arquivo tb_procedimento(.csv/.txt) não encontrado na pasta informada.')

        # Ler tb_procedimento
        header, data = _read_table_flexible(proc_path, encoding=enc)
        if not data:
            raise CommandError('tb_procedimento vazio ou inválido.')
        i_cod, i_nome, i_grup = _detect_columns(header, data)
        if i_cod is None or i_nome is None:
            # Ajuda o usuário a identificar o problema
            preview = data[0] if data else []
            raise CommandError('Colunas CO_PROCEDIMENTO/NO_PROCEDIMENTO não encontradas. Tente fornecer um pacote diferente (com cabeçalho) ou compacte em .zip. Prévia da 1ª linha: ' + ' | '.join(preview))

        # Se solicitado, preparar valores por procedimento
        valores: Dict[str, float] = {}
        if set_valor:
            val_path = _find_table_file(root, 'tb_procedimento_valor')
            if val_path:
                vhead, vrows = _read_table_flexible(val_path, encoding=enc)
                vmap = { _norm(h): idx for idx, h in enumerate(vhead) }
                j_cod = vmap.get('CO_PROCEDIMENTO')
                # competência pode ser CO_COMPETENCIA ou DT_COMPETENCIA (YYYYMM)
                j_comp = vmap.get('CO_COMPETENCIA') or vmap.get('DT_COMPETENCIA')
                j_sh = vmap.get('VL_SH')
                j_sa = vmap.get('VL_SA')
                j_sp = vmap.get('VL_SP')
                by_code: Dict[str, Tuple[str, float]] = {}
                if j_cod is not None:
                    for r in vrows:
                        try:
                            code = (r[j_cod] or '').strip()
                            comp = (r[j_comp] or '').strip() if j_comp is not None else ''
                            def p(i):
                                try:
                                    return float((r[i] or '0').replace(',', '.')) if i is not None else 0.0
                                except Exception:
                                    return 0.0
                            total = p(j_sh) + p(j_sa) + p(j_sp)
                            prev = by_code.get(code)
                            if not prev or comp > prev[0]:
                                by_code[code] = (comp, total)
                        except Exception:
                            continue
                else:
                    # fallback: arquivo sem colunas/cabeçalho, usar heurística linha a linha a partir do arquivo bruto
                    try:
                        with open(val_path, 'r', encoding=enc, newline='') as f:
                            for line in f:
                                parsed = _parse_valor_line_fallback(line)
                                if not parsed:
                                    continue
                                code, comp, total = parsed
                                prev = by_code.get(code)
                                if not prev or comp > prev[0]:
                                    by_code[code] = (comp, total)
                    except Exception:
                        self.stdout.write(self.style.WARNING('Falha no fallback de parsing de valores; valores não serão atualizados.'))
                valores = { k: v for k, (_, v) in by_code.items() }
            else:
                self.stdout.write(self.style.WARNING('tb_procedimento_valor não encontrado; pulando atualização de valores.'))

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for row in data:
                try:
                    cod = (row[i_cod] or '').strip()
                    nome = (row[i_nome] or '').strip()
                    grupo = (row[i_grup] or '').strip() if i_grup is not None else ''
                except Exception:
                    skipped += 1
                    continue

                if not cod or not nome:
                    skipped += 1
                    continue

                # Filtros opcionais
                if not grupo and cod:
                    grupo = cod[:2]
                if only_groups and _norm(grupo) not in only_groups:
                    continue
                if name_terms and not any(term in _norm(nome) for term in name_terms):
                    continue

                # Upsert por codigo_sus
                # Criar sem ativar automaticamente; ativação será manual pela tela
                obj, is_created = TipoExame.objects.get_or_create(codigo_sus=cod, defaults={
                    'nome': nome,
                    'codigo': cod,
                    # não definir 'ativo' aqui; ficará com default do modelo (False)
                })
                # Atualizar campos se já existir
                changed = False
                if not is_created:
                    if obj.nome != nome:
                        obj.nome = nome
                        changed = True
                    if not obj.codigo:
                        obj.codigo = cod
                        changed = True
                    # Não alterar automaticamente o status 'ativo'
                # Valor (opcional)
                if set_valor and cod in valores:
                    try:
                        val = float(valores[cod])
                        if obj.valor != val:
                            obj.valor = val
                            changed = True
                    except Exception:
                        pass
                if is_created:
                    obj.save()
                    created += 1
                elif changed:
                    obj.save()
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Importação concluída. Criados: {created}, Atualizados: {updated}, Ignorados: {skipped}."
        ))
