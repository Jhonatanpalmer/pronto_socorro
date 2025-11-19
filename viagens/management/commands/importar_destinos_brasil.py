import json
import gzip
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand
from django.db import transaction

from viagens.models import DestinoViagem

IBGE_MUNICIPIOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"


class Command(BaseCommand):
    help = (
        "Importa todas as cidades brasileiras a partir da API oficial do IBGE "
        "e cadastra como destinos disponíveis."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--somente-novas",
            action="store_true",
            help="Não reativar cidades já cadastradas, apenas inserir novas entradas.",
        )

    def handle(self, *args, **options):
        somente_novas = options.get("somente_novas", False)
        self.stdout.write("Baixando dados de municípios do IBGE...")

        req = Request(
            IBGE_MUNICIPIOS_URL,
            headers={
                "User-Agent": "sms-iturama/1.0",
                "Accept-Encoding": "gzip, deflate",
            },
        )

        with urlopen(req, timeout=60) as response:
            raw = response.read()
            encoding = response.headers.get("Content-Encoding", "").lower()
            if "gzip" in encoding:
                raw = gzip.decompress(raw)
            texto = raw.decode("utf-8")
            municipios = json.loads(texto)

        if not isinstance(municipios, list):
            self.stderr.write("Resposta inesperada da API do IBGE. Nenhuma cidade foi importada.")
            return

        self.stdout.write(f"{len(municipios)} municípios recebidos. Preparando importação...")

        existentes = {
            (d.nome_cidade.strip().upper(), d.uf.strip().upper()): d
            for d in DestinoViagem.objects.all()
        }

        criar = []
        reativados = 0

        with transaction.atomic():
            for registro in municipios:
                try:
                    nome = (registro.get("nome") or "").strip()
                    uf = (
                        registro.get("microrregiao", {})
                        .get("mesorregiao", {})
                        .get("UF", {})
                        .get("sigla")
                        or ""
                    ).strip()
                except AttributeError:
                    continue

                if not nome or not uf:
                    continue

                chave = (nome.upper(), uf.upper())
                existente = existentes.get(chave)

                if existente is None:
                    criar.append(DestinoViagem(nome_cidade=nome, uf=uf, ativo=True))
                elif not somente_novas and not existente.ativo:
                    existente.ativo = True
                    existente.save(update_fields=["ativo"])
                    reativados += 1

            if criar:
                DestinoViagem.objects.bulk_create(criar, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f"Importação concluída. Novas cidades: {len(criar)}. Cidades reativadas: {reativados}."
        ))
