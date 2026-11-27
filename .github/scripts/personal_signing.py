"""Versioned, reproducible personal APK signing certificate. Never publish the seed or key."""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

ORDER = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551


def identity(seed):
    material = HKDF(
        algorithm=hashes.SHA256(),
        length=48,
        salt=b"mihon-personal-signing-v1",
        info=b"p256-private-key",
    ).derive(seed)
    key = ec.derive_private_key(
        1 + int.from_bytes(material, "big") % (ORDER - 1), ec.SECP256R1()
    )
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Mihon Personal v1")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(datetime(2020, 1, 1, tzinfo=timezone.utc))
        .not_valid_after(datetime(2120, 1, 1, tzinfo=timezone.utc))
        .sign(key, hashes.SHA256(), ecdsa_deterministic=True)
    )
    return key, cert


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        a = identity(b"a" * 32)[1].public_bytes(serialization.Encoding.DER)
        b = identity(b"a" * 32)[1].public_bytes(serialization.Encoding.DER)
        c = identity(b"b" * 32)[1].public_bytes(serialization.Encoding.DER)
        assert a == b and a != c
        return
    seed = os.environ["MIHON_SIGNING_SEED"].encode()
    if len(seed) < 32:
        raise SystemExit("MIHON_SIGNING_SEED must be at least 32 random characters")
    key, cert = identity(seed)
    data = pkcs12.serialize_key_and_certificates(
        b"mihon", key, cert, None, serialization.BestAvailableEncryption(seed)
    )
    path = Path(sys.argv[1])
    path.write_bytes(data)
    path.chmod(0o600)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        print("fingerprint=" + cert.fingerprint(hashes.SHA256()).hex(), file=output)
        print("ready=true", file=output)


if __name__ == "__main__":
    main()
