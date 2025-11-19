from typing import Optional, Dict, Any
import os
from django.conf import settings
from django.db import connections, transaction
from .models import Paciente


def _first_or_none(rows):
    return rows[0] if rows else None


def _ensure_esus_connection(alias: str = 'esus'):
    """Garante uma conexão configurada com o banco e-SUS usando variáveis de ambiente.

    Caso o alias não esteja definido em ``DATABASES``, cria uma entrada temporária
    com base nas variáveis de ambiente ``ESUS_DB_*``.
    """

    dbs = connections.databases
    if alias in dbs:
        return connections[alias]

    name = os.getenv('ESUS_DB_NAME')
    if not name:
        raise RuntimeError('Conexão com o e-SUS não configurada. Defina as variáveis ESUS_DB_NAME/USER/PASSWORD/HOST/PORT.')

    dbs[alias] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': name,
        'USER': os.getenv('ESUS_DB_USER', 'postgres'),
        'PASSWORD': os.getenv('ESUS_DB_PASSWORD', ''),
        'HOST': os.getenv('ESUS_DB_HOST', 'localhost'),
        'PORT': os.getenv('ESUS_DB_PORT', '5432'),
    }
    return connections[alias]


def get_esus_connection():
    alias = getattr(settings, 'ESUS_DB_ALIAS', 'esus')
    return _ensure_esus_connection(alias)


def buscar_paciente_esus(cpf: Optional[str] = None, cns: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Busca dados do paciente no e-SUS AB via API.
    
    Args:
        cpf: CPF do paciente (opcional)
        cns: CNS do paciente (opcional)
    
    Returns:
        dict: Dados do paciente encontrado ou None se não encontrado
        
    Observações:
    - Campos estruturados de endereço são preenchidos individualmente.
    """
    if not cpf and not cns:
        return None
    where = []
    params = []
    if cpf:
        where.append("cpf = %s")
        params.append(''.join(filter(str.isdigit, cpf)))
    if cns:
        where.append("cns = %s")
        params.append(cns)
    sql = f"""
        SELECT nome, cpf, cns, data_nascimento, nome_mae, nome_pai,
               logradouro, numero, bairro, cep, telefone
        FROM esus_pacientes_view
        WHERE {' OR '.join(where)}
        ORDER BY data_nascimento DESC
        LIMIT 1
    """
    try:
        conn = get_esus_connection()
        with conn.cursor() as cur:
            # Set client encoding to UTF-8
            cur.execute("SET client_encoding TO 'UTF8'")
            cur.execute(sql, params)
            rows = cur.fetchall()
            if not rows:
                return None
            # Mapear pelo índice, ajuste conforme sua view real
            r = rows[0]
            return {
                'nome': r[0],
                'cpf': r[1],
                'cns': r[2],
                'data_nascimento': r[3],
                'nome_mae': r[4] or '',
                'nome_pai': r[5] or '',
                'logradouro': r[6] or '',
                'numero': r[7] or '',
                'bairro': r[8] or '',
                'cep': r[9] or '',
                'telefone': r[10] or '',
            }
    except UnicodeDecodeError as e:
        print(f"Erro de codificação UTF-8: {e}")
        return None
    except Exception as e:
        print(f"Erro ao buscar dados no e-SUS: {e}")
        return None


@transaction.atomic
def atualizar_paciente_com_esus(paciente: Paciente, dados: Dict[str, Any], sobrescrever: bool = False) -> Paciente:
    """Atualiza campos do Paciente local com dados vindos do e-SUS.

    - Quando sobrescrever=False, apenas preenche campos vazios.
    - Campo 'endereco' livre será montado a partir de logradouro/numero/bairro (se estiver vazio).
    """
    def set_field(obj, field, value):
        current = getattr(obj, field)
        if sobrescrever or not current:
            setattr(obj, field, value)

    set_field(paciente, 'nome', dados.get('nome'))
    set_field(paciente, 'cpf', ''.join(filter(str.isdigit, dados.get('cpf') or '')) or None)
    set_field(paciente, 'cns', dados.get('cns'))
    set_field(paciente, 'data_nascimento', dados.get('data_nascimento'))
    set_field(paciente, 'nome_mae', dados.get('nome_mae'))
    set_field(paciente, 'nome_pai', dados.get('nome_pai'))
    set_field(paciente, 'logradouro', dados.get('logradouro'))
    set_field(paciente, 'numero', dados.get('numero'))
    set_field(paciente, 'bairro', dados.get('bairro'))
    set_field(paciente, 'cep', dados.get('cep'))
    set_field(paciente, 'telefone', dados.get('telefone'))

    paciente.save()
    return paciente
