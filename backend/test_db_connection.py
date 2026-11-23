
from app.services.postgres_vector_service import _connection


def main():
    print("Verificando conexão com PostgreSQL...")

    with _connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    current_database() AS database_name,
                    current_user AS database_user
                """
            )

            result = cursor.fetchone()

            print("Conexão estabelecida!")
            print(
                "Banco:",
                result["database_name"],
            )
            print(
                "Usuário PostgreSQL:",
                result["database_user"],
            )

            cursor.execute(
                """
                SELECT
                    to_regclass(
                        'public.media_files'
                    ) IS NOT NULL AS media_files_exists,
                    to_regclass(
                        'public.transcript_chunks'
                    ) IS NOT NULL AS chunks_exists
                """
            )

            tables = cursor.fetchone()

            print(
                "Tabela media_files:",
                tables["media_files_exists"],
            )
            print(
                "Tabela transcript_chunks:",
                tables["chunks_exists"],
            )


if __name__ == "__main__":
    main()
