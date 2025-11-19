from django.core.management.base import BaseCommand
from pacientes.services import get_esus_connection


class Command(BaseCommand):
    help = "Consulta todos os registros de tb_cidadao no banco 'esus'. Use --limit para limitar a quantidade."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Número máximo de registros para exibir (padrão: 100). Use 0 para sem limite.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        conn = get_esus_connection()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM tb_cidadao"
            if limit and limit > 0:
                sql += f" LIMIT {int(limit)}"
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # Exibe um resumo em formato simples (CSV-like)
        if not rows:
            self.stdout.write(self.style.WARNING("Nenhum registro encontrado em tb_cidadao."))
            return

        # imprime cabeçalhos
        self.stdout.write(",".join(columns))
        for row in rows:
            # Converte valores None para string vazia e outros para str
            values = ["" if v is None else str(v) for v in row]
            self.stdout.write(",".join(values))

        self.stdout.write(self.style.SUCCESS(f"Total exibido: {len(rows)} registro(s)."))
