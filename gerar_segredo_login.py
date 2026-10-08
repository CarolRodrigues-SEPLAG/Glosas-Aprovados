"""Generate a Streamlit secrets.toml block without saving the password."""

from __future__ import annotations

import getpass
import hashlib
import re
import secrets


_PBKDF2_ITERATIONS = 600_000


def main() -> None:
    username = input("Usuário compartilhado: ").strip()
    if re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", username) is None:
        raise SystemExit(
            "Use de 1 a 64 caracteres: letras sem acento, números, ponto, "
            "hífen ou sublinhado."
        )

    password = getpass.getpass("Senha (não será exibida): ")
    confirmation = getpass.getpass("Confirme a senha: ")
    if not password:
        raise SystemExit("A senha não pode ficar vazia.")
    if password != confirmation:
        raise SystemExit("As senhas não coincidem.")

    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    print("\nCopie o bloco abaixo para Streamlit secrets:")
    print(f'username = "{username}"')
    print(f'password_salt = "{salt.hex()}"')
    print(f'password_hash = "{password_hash.hex()}"')


if __name__ == "__main__":
    main()
