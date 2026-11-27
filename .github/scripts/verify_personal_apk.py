"""Check the actual APK, supporting both old and new apksigner output."""
import re
import sys
from pathlib import Path
from zipfile import ZipFile

DIGEST = re.compile(
    r"^(?:Signer #\d+|V[\d.]+ Signer:?) certificate SHA-256 digest: ([a-fA-F0-9]{64})\s*$",
    re.MULTILINE,
)


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def verify_certificate(report, expected):
    digests = {x.lower() for x in DIGEST.findall(report)}
    require(
        digests == {expected.lower()},
        f"Certificate mismatch: expected {expected}, got {sorted(digests)}",
    )
    counts = re.findall(r"^Number of signers: (\d+)\s*$", report, re.MULTILINE)
    require(counts == ["1"], f"Expected exactly one signer, got {counts}")
    print("Certificate verified:", expected)


def main():
    if sys.argv[1:] == ["--self-test"]:
        digest = "a" * 64
        for prefix in ("Signer #1", "V2 Signer:", "V3.1 Signer:"):
            verify_certificate(
                f"Number of signers: 1\n{prefix} certificate SHA-256 digest: {digest}\n",
                digest,
            )
        for report in (
            f"Number of signers: 1\nV2 Signer: certificate SHA-256 digest: {'b' * 64}\n",
            f"Number of signers: 2\nSigner #1 certificate SHA-256 digest: {digest}\n",
            "Number of signers: 1\n",
        ):
            try:
                verify_certificate(report, digest)
            except SystemExit:
                pass
            else:
                raise AssertionError("Invalid certificate report accepted")
        return

    apk, report, expected, mapping = sys.argv[1:]
    verify_certificate(Path(report).read_text(), expected)
    with ZipFile(apk) as archive:
        abis = {
            path.split("/")[1]
            for path in archive.namelist()
            if re.fullmatch(r"lib/[^/]+/[^/]+\.so", path)
        }
        require(abis == {"arm64-v8a"}, f"Unexpected native ABIs: {sorted(abis)}")
        require(
            "assets/selective_white.wgsl" in archive.namelist(),
            "Built-in selective white shader is missing",
        )
    require(Path(mapping).is_file() and Path(mapping).stat().st_size > 0, "R8 mapping missing")
    print("ARM64-only APK, shader asset and R8 mapping verified.")


if __name__ == "__main__":
    main()
