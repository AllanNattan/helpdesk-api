from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import User

EMAIL_ADAPTER = TypeAdapter(EmailStr)
ALLOWED_ROLES = {"agent", "admin"}


def main() -> int:
    print("Cadastro administrativo da HelpDesk API")
    print("Este comando cria somente agentes ou administradores.\n")

    name = input("Nome completo: ").strip()

    if not 2 <= len(name) <= 120:
        print("Erro: o nome deve ter entre 2 e 120 caracteres.")
        return 1

    raw_email = input("E-mail: ").strip()

    try:
        email = str(EMAIL_ADAPTER.validate_python(raw_email)).lower()
    except ValidationError:
        print("Erro: informe um endereço de e-mail válido.")
        return 1

    role = input("Perfil (agent/admin): ").strip().lower()

    if role not in ALLOWED_ROLES:
        print("Erro: o perfil deve ser 'agent' ou 'admin'.")
        return 1

    password = getpass("Senha (12 a 128 caracteres): ")

    if not 12 <= len(password) <= 128:
        print("Erro: a senha deve ter entre 12 e 128 caracteres.")
        return 1

    password_confirmation = getpass("Confirme a senha: ")

    if password != password_confirmation:
        print("Erro: as senhas não coincidem.")
        return 1

    try:
        with SessionLocal() as db:
            existing_user = db.scalar(
                select(User.id).where(User.email == email)
            )

            if existing_user is not None:
                print("Erro: já existe uma conta com esse e-mail.")
                return 1

            user = User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=role,
            )

            db.add(user)

            try:
                db.commit()
                db.refresh(user)
            except IntegrityError:
                db.rollback()
                print("Erro: já existe uma conta com esse e-mail.")
                return 1
            except SQLAlchemyError:
                db.rollback()
                print("Erro: não foi possível salvar o usuário no banco.")
                return 1

            print("\nUsuário criado com sucesso.")
            print(f"ID: {user.id}")
            print(f"E-mail: {user.email}")
            print(f"Perfil: {user.role}")

    except SQLAlchemyError:
        print("Erro: não foi possível conectar ao banco de dados.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())