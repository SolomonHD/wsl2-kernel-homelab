# Validation and acceptance

A catalog record becomes `validated` only when both tracked reports say `Result: PASS`, their
manifest statuses are `pass`, artifact identity is unchanged, and every acceptance check below has
recorded commands, versions, UTC time, actual output, and cleanup.

## Build evidence

Record the exact upstream tag and commit, shallow/pristine status, config merge and `olddefconfig`,
required-symbol validation, compiler identity, kernel/modules build, `make kernelrelease`, matching
`modules/lib/modules/<release>`, `INSTALL_MOD_STRIP=1`, absence of staged `.debug*` ELF sections,
canonical artifact filenames, exact byte sizes, and SHA-256 checksums. Recompute sizes and checksums
from the exact release inputs. Any mismatch is `Result: FAIL` and moves the manifest to `failed`
with the stage and reason.

## Runtime acceptance

Run destructive network checks only in an isolated test distribution and clean up temporary links,
chains, containers, networks, and rules.

```bash
uname -r
modprobe wireguard
ip link add wg-openspec type wireguard
ip link del wg-openspec
ip -6 address show
ip -6 route show
ip -6 rule show
docker info --format '{{.Driver}}'
docker run --rm hello-world
docker network create openspec-test
docker run -d --rm --name openspec-a --network openspec-test busybox sleep 300
docker run --rm --network openspec-test busybox ping -c 1 openspec-a
docker rm -f openspec-a
docker network rm openspec-test
```

Docker must report overlay storage, start containers, create a bridge and veth pair, connect two
containers, and make a disposable published port reachable through the WSL network path. Record the
published-port command and probe appropriate to the test distribution.

For CONNMARK, use a uniquely named temporary mangle chain, install both `--save-mark` and
`--restore-mark`, list them without unsupported match/target errors, then remove the chain. Run the
equivalent IPv4 and IPv6 firewall/NAT probes for the distribution's iptables or nftables backend.
Do not alter production firewall chains for acceptance testing.

If WireGuard, IPv6, Docker, overlayfs, bridge/NAT, or CONNMARK fails, mark the report `Result: FAIL`,
set its manifest validation status to `fail`, set lifecycle `failed`, and record the failed stage and
reason. Never publish partial acceptance. The normative criteria are in the
[`wsl2-kernel-build` spec](../openspec/specs/wsl2-kernel-build/spec.md)
and [`validated release` spec](../openspec/specs/validated-kernel-release/spec.md).

After successful evidence updates, run:

```bash
python3 scripts/catalog.py validate
python3 scripts/release.py preflight --tag linux-msft-wsl-6.18.35.2 --artifacts build/linux-msft-wsl-6.18.35.2
```

Success prints a passing preflight. Failure names the missing evidence or checksum and blocks release.
Users moving from another kernel should complete
[`wsl-kernel-migration.md`](wsl-kernel-migration.md) before recording new runtime evidence.
