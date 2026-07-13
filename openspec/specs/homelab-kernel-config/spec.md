# Homelab kernel configuration

## Purpose

Define the pinned Microsoft WSL2 kernel baseline and configuration contract for WireGuard, IPv6,
Docker networking, and CONNMARK workloads.

## Requirements

### Requirement: Pinned Microsoft WSL2 kernel baseline
The homelab kernel configuration SHALL target the exact Microsoft tag `linux-msft-wsl-6.18.35.2` at commit `1bd4ed3d4ada93738eef3fc2a66b674c640dc326` and SHALL use that tag's `arch/x86/configs/config-wsl` as its base configuration.

#### Scenario: Baseline identity is verified
- **WHEN** a homelab kernel configuration is generated
- **THEN** the source checkout resolves to tag `linux-msft-wsl-6.18.35.2`
- **AND** `HEAD` equals commit `1bd4ed3d4ada93738eef3fc2a66b674c640dc326`

### Requirement: WireGuard server support
The configuration SHALL set `CONFIG_WIREGUARD=m` while retaining the cryptographic dependencies selected by the Microsoft WSL2 base configuration. The matching WireGuard module MUST be included in the deployed modules VHDX.

#### Scenario: WireGuard interface is available
- **WHEN** the built kernel and matching modules VHDX are running in WSL2
- **THEN** `modprobe wireguard` succeeds
- **AND** a temporary WireGuard interface can be created and removed with `ip link`

### Requirement: IPv6 routing support
The configuration SHALL set `CONFIG_IPV6=y`, `CONFIG_IPV6_MULTIPLE_TABLES=y`, `CONFIG_IPV6_ROUTER_PREF=y`, `CONFIG_IPV6_ROUTE_INFO=y`, `CONFIG_IPV6_SUBTREES=y`, `CONFIG_IPV6_MROUTE=y`, and `CONFIG_IPV6_PIMSM_V2=y`.

#### Scenario: IPv6 policy routing is available
- **WHEN** the built kernel is running in WSL2
- **THEN** IPv6 addresses and routes can be enumerated
- **AND** `ip -6 rule` reports IPv6 policy-routing rules

### Requirement: Container isolation and storage support
The configuration SHALL set `CONFIG_CGROUPS=y`, `CONFIG_MEMCG=y`, `CONFIG_BLK_CGROUP=y`, `CONFIG_CGROUP_PIDS=y`, `CONFIG_CGROUP_BPF=y`, `CONFIG_NAMESPACES=y`, `CONFIG_UTS_NS=y`, `CONFIG_IPC_NS=y`, `CONFIG_PID_NS=y`, `CONFIG_NET_NS=y`, `CONFIG_SECCOMP=y`, `CONFIG_BPF_SYSCALL=y`, and `CONFIG_OVERLAY_FS=y`.

#### Scenario: Docker container starts with resource isolation
- **WHEN** Docker starts under the built kernel and runs a disposable container
- **THEN** the container uses kernel namespaces and cgroups without capability errors
- **AND** Docker's overlay storage driver initializes successfully

### Requirement: Container network devices
The configuration SHALL set `CONFIG_VETH=y` and `CONFIG_VXLAN=y`, and SHALL set `CONFIG_BRIDGE=m`, `CONFIG_BRIDGE_NETFILTER=m`, `CONFIG_TUN=m`, and `CONFIG_TAP=m`. All modular network devices MUST be included in the matching modules VHDX.

#### Scenario: Docker bridge networking is operational
- **WHEN** Docker creates a bridge network and starts two disposable containers on it
- **THEN** the bridge and veth devices are created successfully
- **AND** the containers can communicate across that network

### Requirement: Netfilter, NAT, and CONNMARK support
The configuration SHALL set `CONFIG_NETFILTER=y`, `CONFIG_NETFILTER_XTABLES=y`, `CONFIG_NF_CONNTRACK=y`, `CONFIG_NF_CONNTRACK_MARK=y`, `CONFIG_NF_NAT=y`, `CONFIG_NF_TABLES=y`, `CONFIG_NFT_NAT=y`, and `CONFIG_NFT_MASQ=y`. It SHALL set `CONFIG_NETFILTER_XT_TARGET_CONNMARK=m`, `CONFIG_NETFILTER_XT_MATCH_CONNMARK=m`, `CONFIG_NETFILTER_XT_TARGET_MARK=m`, `CONFIG_NETFILTER_XT_TARGET_MASQUERADE=m`, `CONFIG_NETFILTER_XT_TARGET_REDIRECT=m`, `CONFIG_NETFILTER_XT_MATCH_ADDRTYPE=m`, `CONFIG_NETFILTER_XT_MATCH_CONNTRACK=m`, and `CONFIG_NETFILTER_XT_MATCH_MARK=m`.

#### Scenario: Connection marks can be saved and restored
- **WHEN** the matching xtables modules are loaded
- **THEN** an isolated iptables mangle chain accepts CONNMARK save-mark and restore-mark rules
- **AND** the rules can be listed without an unsupported-target error

### Requirement: IPv4 and IPv6 firewall compatibility
The configuration SHALL set `CONFIG_IP_NF_IPTABLES=m`, `CONFIG_IP_NF_FILTER=m`, `CONFIG_IP_NF_MANGLE=m`, `CONFIG_IP_NF_TARGET_MASQUERADE=m`, `CONFIG_IP6_NF_IPTABLES=m`, `CONFIG_IP6_NF_FILTER=m`, `CONFIG_IP6_NF_MANGLE=m`, and `CONFIG_IP6_NF_NAT=m`. These modules MUST be included in the matching modules VHDX so Docker can use either nftables-backed or legacy iptables tooling.

#### Scenario: Docker programs firewall and NAT rules
- **WHEN** Docker starts with IPv4 and IPv6 networking enabled
- **THEN** it creates the required filter and NAT rules without missing table, match, or target errors
- **AND** a published container port is reachable through the WSL2 network path

### Requirement: Generated configuration validation
The final generated `.config` SHALL be normalized with `olddefconfig` and SHALL be checked against every required `CONFIG_*` value before compilation.

#### Scenario: Required symbol drifts from contract
- **WHEN** `olddefconfig` changes or disables a required symbol
- **THEN** configuration validation fails before the kernel build starts
- **AND** the mismatched symbol and actual value are reported
