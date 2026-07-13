# Runtime validation: `linux-msft-wsl-6.18.35.2`

Result: PASS

- UTC test time: `2026-07-13T20:37:40Z`
- WSL: `2.7.10.0` on Windows `10.0.26200.8737`
- Distribution: Ubuntu `22.04.5 LTS` (WSL 2)
- Kernel: `6.18.35.2-microsoft-standard-WSL2+`
- Docker Desktop engine and client: `29.6.1`; containerd `2.2.5`; runc `1.3.6`
- Docker storage driver: `overlay2`
- iproute2: `5.15.0`; iptables/ip6tables: `1.8.7 (nf_tables)`; kmod: `29`
- WireGuard: matching kernel module loaded successfully; `wireguard-tools` was not required for
  the `ip link` interface-creation probe.

| Check | Acceptance | Actual | Result |
| --- | --- | --- | --- |
| Identity | `uname -r` equals manifest kernel release | `6.18.35.2-microsoft-standard-WSL2+` | PASS |
| Modules | module tree release equals kernel release | `wireguard.ko` path and vermagic match the running release | PASS |
| WireGuard | module loads and temporary interface works | `modprobe` and disposable `wg-openspec` creation/deletion succeeded | PASS |
| IPv6 | addresses, routes, and policy rules enumerate | Global/link addresses, default route, and local/main rules present | PASS |
| Docker | daemon starts and disposable container runs | Docker Desktop `29.6.1`; `hello-world` completed | PASS |
| Overlayfs | Docker reports overlay storage | `overlay2` | PASS |
| Bridge | two containers communicate over a user bridge | BusyBox peer replied with 0% packet loss; bridge and veth were present | PASS |
| Published-port NAT | disposable service is reachable | `127.0.0.1:55502` returned `openspec-ok` | PASS |
| IPv4 firewall/NAT | temporary nft-fronted chains install and list | Unreferenced mangle and NAT chains listed successfully | PASS |
| IPv6 firewall/NAT | temporary nft-fronted chains install and list | Unreferenced mangle and NAT chains listed successfully | PASS |
| CONNMARK | isolated save/restore rules install and list | Both rules listed for IPv4 and IPv6 in `OSPEC_ROOT_R` | PASS |

## Artifact identity

The active `%UserProfile%\.wslconfig` set both paths in the same `[wsl2]` section:

```ini
kernel=C:\\Users\\Solom\\WSL2Kernel\\linux-msft-wsl-6.18.35.2
kernelModules=C:\\Users\\Solom\\WSL2Kernel\\modules-linux-msft-wsl-6.18.35.2.vhdx
```

The deployed Windows artifacts matched the manifest exactly:

```text
b8ab38766bd36897ebdd629120bea9c1b779e442a9a81897b0ebaedb0bbfc435  linux-msft-wsl-6.18.35.2 (17322496 bytes)
c0cd43237a0747d75c663e333cb4912a9077d7e26093de418cec8fc5b665385f  modules-linux-msft-wsl-6.18.35.2.vhdx (226492416 bytes)
```

`/lib/modules/6.18.35.2-microsoft-standard-WSL2+` existed after restart. The WireGuard module path
and vermagic were:

```text
/lib/modules/6.18.35.2-microsoft-standard-WSL2+/kernel/drivers/net/wireguard/wireguard.ko
6.18.35.2-microsoft-standard-WSL2+ SMP preempt mod_unload modversions
```

## Commands and observed results

Privileged kernel and firewall probes used WSL's root launch in the Ubuntu test distribution:

```powershell
wsl.exe -d Ubuntu -u root -- modprobe wireguard
wsl.exe -d Ubuntu -u root -- ip link add wg-openspec type wireguard
wsl.exe -d Ubuntu -u root -- ip -d link show wg-openspec
wsl.exe -d Ubuntu -u root -- ip link del wg-openspec
wsl.exe -d Ubuntu -u root -- modinfo -F filename wireguard
wsl.exe -d Ubuntu -u root -- modinfo -F vermagic wireguard
```

IPv6 state was enumerated inside the restarted distribution:

```bash
ip -6 address show
ip -6 route show
ip -6 rule show
```

Both `iptables` and `ip6tables` used the nft frontend. For each frontend, the test created an
unreferenced temporary mangle chain containing `CONNMARK --save-mark` and
`CONNMARK --restore-mark`, plus an unreferenced NAT chain containing `RETURN`, listed them, and
then flushed and deleted them. The CONNMARK rules reported:

```text
-N OSPEC_ROOT_R
-A OSPEC_ROOT_R -j CONNMARK --save-mark --nfmask 0xffffffff --ctmask 0xffffffff
-A OSPEC_ROOT_R -j CONNMARK --restore-mark --nfmask 0xffffffff --ctmask 0xffffffff
```

Docker acceptance used disposable containers and a user bridge:

```bash
docker info --format 'driver={{.Driver}} server={{.ServerVersion}} kernel={{.KernelVersion}}'
docker run --rm hello-world
docker network create openspec-test
docker run -d --rm --name openspec-a --network openspec-test busybox sleep 300
docker run --rm --network openspec-test busybox ping -c 1 openspec-a
docker run -d --rm --name openspec-http -p 127.0.0.1::80 busybox \
  sh -c 'mkdir -p /www; echo openspec-ok > /www/index.html; exec httpd -f -p 80 -h /www'
curl http://127.0.0.1:55502/
```

Docker reported:

```text
driver=overlay2 server=29.6.1 kernel=6.18.35.2-microsoft-standard-WSL2+
PING openspec-a (172.20.0.2): 56 data bytes
1 packets transmitted, 1 packets received, 0% packet loss
published_port=55502 response=openspec-ok
```

All temporary WireGuard links, IPv4/IPv6 firewall chains, containers, and Docker networks were
removed. Post-cleanup checks found no `wg-openspec` link, `OSPEC_ROOT_R` chain, `openspec-*`
container, or `openspec-test` network.
