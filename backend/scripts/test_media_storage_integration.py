
import os
import tempfile
import uuid

from app.services.media_storage_service import (
    upload_media_file,
    download_media_file,
    delete_media_file,
)


def main():
    owner_id = str(uuid.UUID(
        os.environ["TEST_OWNER_A"]
    ))
    job_id = str(uuid.uuid4())

    content = (
        b"JURIDICAL_AI_STORAGE_TEST_"
        + os.urandom(128)
    )

    source_path = None
    downloaded_path = None
    storage_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".mp4",
            delete=False,
        ) as source:
            source.write(content)
            source_path = source.name

        storage_path = upload_media_file(
            local_file_path=source_path,
            owner_user_id=owner_id,
            job_id=job_id,
            original_filename="teste_storage.mp4",
        )

        print("[OK] Upload privado realizado")

        downloaded_path = download_media_file(
            storage_path=storage_path,
            owner_user_id=owner_id,
            job_id=job_id,
        )

        with open(downloaded_path, "rb") as file:
            downloaded_content = file.read()

        assert downloaded_content == content

        print("[OK] Download íntegro")

        other_user = str(uuid.uuid4())

        try:
            download_media_file(
                storage_path=storage_path,
                owner_user_id=other_user,
                job_id=job_id,
            )
        except ValueError:
            print("[OK] Caminho de outro usuário rejeitado")
        else:
            raise AssertionError(
                "Falha no isolamento do caminho."
            )

        assert delete_media_file(
            storage_path=storage_path,
            owner_user_id=owner_id,
            job_id=job_id,
        )

        print("[OK] Arquivo remoto excluído")

        storage_path = None

        print()
        print("SUCESSO: integração Storage validada.")

    finally:
        for path in (source_path, downloaded_path):
            if path and os.path.isfile(path):
                os.remove(path)

        if storage_path:
            try:
                delete_media_file(
                    storage_path=storage_path,
                    owner_user_id=owner_id,
                    job_id=job_id,
                )
                print("[OK] Limpeza remota realizada")
            except Exception:
                print(
                    "[ATENÇÃO] Limpeza remota falhou. "
                    f"Verifique o objeto: {storage_path}"
                )


if __name__ == "__main__":
    main()
