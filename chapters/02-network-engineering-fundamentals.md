# Chapter 2: Network Engineering Fundamentals

> **Estimated Time: 3-4 hours** | **Prerequisites: Basic Linux, TCP/IP awareness**

---

## 🎯 Learning Objectives

By the end of this chapter, you will be able to:

1. **Master the OSI & TCP/IP models** and their practical implications
2. **Configure and troubleshoot** IP addressing, subnetting, routing
3. **Implement secure transport** with TLS 1.3 and modern protocols
4. **Architect modern data center networks** (spine-leaf, EVPN-VXLAN)
5. **Design multi-region WAN** architectures (BGP, SD-WAN, hybrid cloud)
6. **Apply zero-trust network** principles and segmentation
7. **Use traffic analysis tools** (tcpdump, Wireshark, iperf) confidently

---

## 2.1 Network Models

### OSI vs TCP/IP Reference Model

```
┌─────────────────┬─────────────────────┬─────────────────────┐
│    OSI 7-Layer  │      TCP/IP         │   Common Protocols   │
├─────────────────┼─────────────────────┼─────────────────────┤
│ 7. Application  │                     │ HTTP, gRPC, DNS,     │
│ 6. Presentation │   Application       │ SMTP, SSH, MQTT,    │
│ 5. Session      │                     │ WebSocket, gRPC     │
├─────────────────┼─────────────────────┼─────────────────────┤
│ 4. Transport    │   Transport (Host)  │ TCP, UDP, QUIC      │
├─────────────────┼─────────────────────┼─────────────────────┤
│ 3. Network      │   Internet          │ IP (v4/v6), ICMP,   │
│                 │                     │ OSPF, BGP, MPLS    │
├─────────────────┼─────────────────────┼─────────────────────┤
│ 2. Data Link    │   Network Access    │ Ethernet, Wi-Fi,    │
│                 │   (Link)            │ ARP, PPP, VLAN,    │
│ 1. Physical     │                     │ MAC, 802.1Q         │
└─────────────────┴─────────────────────┴─────────────────────┘
```

### Data Encapsulation (How a Packet Travels)

```
┌──────────────────────────────────────────────────────────┐
│ Application Data (e.g., HTTP GET /index.html)           │
├──────────────────────────────────────────────────────────┤
│ TCP Header (Src/Dst Port, Seq, Ack, Flags, Checksum)   │  ← L4
├──────────────────────────────────────────────────────────┤
│ IP Header (Src/Dst IP, TTL, Protocol=TCP)              │  ← L3
├──────────────────────────────────────────────────────────┤
│ Ethernet Header (Src/Dst MAC, EtherType=0x0800)        │  ← L2
├──────────────────────────────────────────────────────────┤
│ Preamble/SFD (7+1 bytes for sync)                       │  ← L1
└──────────────────────────────────────────────────────────┘

Sent bits → Receiver reverses → Application receives data
```

> **💡 Interview Tip**: Always frame problems at the correct layer. "Why is my app slow?" — could be DNS (L7), TCP retransmits (L4), route flapping (L3), or duplex mismatch (L2).

---

## 2.2 IPv4 Addressing & Subnetting

### Address Classes & CIDR

| Class | Range | Default Mask | CIDR | Hosts |
|-------|-------|--------------|------|-------|
| A | 10.0.0.0 – 10.255.255.255 | 255.0.0.0 | /8 | 16,777,214 |
| B | 172.16.0.0 – 172.31.255.255 | 255.255.0.0 | /12 | 1,048,574 |
| C | 192.168.0.0 – 192.168.255.255 | 255.255.255.0 | /16 | 65,534 |
| Loopback | 127.0.0.0 – 127.255.255.255 | /8 | — |
| Link-Local | 169.254.0.0 – 169.254.255.255 | /16 | — |
| Private RFC 1918 | 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 | — | — |

### Subnetting Cheat Sheet

```
192.168.1.0/26 → ? hosts
  /26 means: 32 - 26 = 6 host bits
  Subnets: 2^6 = 64 subnets (if /26 subnetted from /24)
  Hosts: 2^6 - 2 = 62 usable per subnet
  Subnet mask: 255.255.255.192
  Subnets in /24:
    192.168.1.0/26   (0-63)
    192.168.1.64/26  (64-127)
    192.168.1.128/26 (128-191)
    192.168.1.192/26 (192-255)

Power of 2 reference:
/30 = 4 IPs (2 hosts)   — point-to-point links
/29 = 8 IPs (6 hosts)   — small point-to-point
/28 = 16 IPs (14 hosts) — small office
/27 = 32 IPs (30 hosts)
/26 = 64 IPs (62 hosts)
/25 = 128 IPs (126 hosts)
/24 = 256 IPs (254 hosts) — typical office/segment
/23 = 512 IPs (510 hosts)
/22 = 1024 IPs (1022 hosts)
/20 = 4096 IPs (4094 hosts)
/16 = 65536 IPs (65534 hosts)
```

### Subnet Design Best Practices

```
┌────────────────────────────────────────────────────────────────┐
│              Hierarchical Subnet Allocation                     │
├────────────────────────────────────────────────────────────────┤
│ 10.0.0.0/8     — Enterprise Superblock                         │
│   ├─ 10.0.0.0/16   — Region / Datacenter 1                     │
│   │   ├─ 10.0.0.0/24   — DC1 Management                       │
│   │   ├─ 10.0.1.0/24   — DC1 Spine-Leaf                        │
│   │   ├─ 10.0.2.0/24   — DC1 Servers (Web Tier)                │
│   │   ├─ 10.0.3.0/24   — DC1 Servers (App Tier)                │
│   │   └─ 10.0.4.0/24   — DC1 Servers (DB Tier)                 │
│   ├─ 10.1.0.0/16   — Region / Datacenter 2                     │
│   ├─ 10.10.0.0/16  — DMZ / Public-facing                       │
│   ├─ 10.20.0.0/16  — User VLANs / Office                       │
│   └─ 10.30.0.0/16  — Site-to-site VPN                          │
└────────────────────────────────────────────────────────────────┘

Tools: sipcalc, subnetcalc, ipcalc, subnet-design-tools
```

---

## 2.3 IPv6 — The Future (and Present)

### Why IPv6?

- **Exhaustion**: IANA exhausted IPv4 in 2011, RIRs followed
- **Header simplicity**: No fragmentation, simpler forwarding
- **Built-in**: SLAAC, IPsec, no NAT needed (E2E principle)
- **Scale**: 2¹²⁸ addresses (~3.4×10³⁸)

### Address Types

| Type | Prefix | Example | Scope |
|------|--------|---------|-------|
| Global Unicast | 2000::/3 | 2001:db8::1 | Internet |
| Unique Local (ULA) | fc00::/7 | fd00::/8 | Private |
| Link-Local | fe80::/10 | fe80::1 | One link only |
| Loopback | ::1/128 | ::1 | Localhost |
| Multicast | ff00::/8 | ff02::1 (all nodes) | Group |

### IPv6 Header (Simpler than IPv4)

```
┌─────────────────────┬────────────────────┐
│ Version (4) | Traffic Class (8) | Flow Label (20) │  4 bytes
├─────────────────────┴────────────────────┤
│ Payload Length (16) | Next Header (8) | Hop Limit (8) │  4 bytes
├─────────────────────────────────────────┤
│           Source Address (128)            │  16 bytes
├─────────────────────────────────────────┤
│       Destination Address (128)           │  16 bytes
└─────────────────────────────────────────┘
Total: 40 bytes fixed (vs 20-60 bytes IPv4)
```

### Dual-Stack & Transition Mechanisms

| Mechanism | Purpose | When to Use |
|-----------|---------|-------------|
| **Dual-stack** | Run IPv4 + IPv6 simultaneously | Recommended transition |
| **NAT64/DNS64** | IPv6-only hosts access IPv4 services | Mobile carriers |
| **464XLAT** | Translation for IPv4-only apps | Mobile carriers |
| **6rd** | IPv6 over IPv4 tunnels | ISP transition |
| **DS-Lite** | IPv4 over IPv6 tunnels | IPv6-first networks |

---

## 2.4 Routing Protocols

### Static vs Dynamic Routing

```
┌──────────────────────────────────────────────────────────────┐
│                      ROUTING HIERARCHY                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────┐                                          │
│  │  BGP (Path-Vec)│  ← Between Autonomous Systems (ASNs)    │
│  └────────┬───────┘                                          │
│           │                                                  │
│  ┌────────▼───────┐                                          │
│  │  IGP (Interior)│  ← Within Autonomous System              │
│  │  • OSPF (LS)   │                                          │
│  │  • IS-IS (LS)  │                                          │
│  │  • EIGRP (DV)  │                                          │
│  │  • RIP (DV)    │                                          │
│  └────────────────┘                                          │
└──────────────────────────────────────────────────────────────┘
```

### Distance-Vector vs Link-State

| Property | Distance-Vector (RIP, EIGRP) | Link-State (OSPF, IS-IS) |
|----------|------------------------------|---------------------------|
| View | Neighbor's view only | Full topology map |
| Convergence | Slow (RIP), faster (EIGRP) | Fast |
| CPU/Memory | Low | Higher |
| Scalability | Limited | Better |
| Algorithm | Bellman-Ford | Dijkstra (SPF) |
| Loops | Count-to-infinity | None (with split horizon) |

### BGP — The Backbone of the Internet

```yaml
# BGP Message Types
OPEN:        Establishes peer session (AS, Router ID, Hold Time)
UPDATE:      Advertises new/withdrawn routes + path attributes
KEEPALIVE:   Maintains session (60s default)
NOTIFICATION: Errors → session reset

# Path Attributes (Selection Order)
1. WEIGHT (Cisco proprietary, local preference)
2. LOCAL_PREF (within AS)
3. ORIGIN (IGP, EGP, Incomplete)
4. AS_PATH (shorter wins)
5. ORIGINATOR_ID
6. CLUSTER_LIST
7. MED (Multi-Exit Discriminator)
8. eBGP > iBGP
9. IGP metric to next-hop
10. Router ID (older wins)

# Sample BGP Configuration (Cisco)
router bgp 65001
 bgp router-id 1.1.1.1
 neighbor 10.0.0.2 remote-as 65002
 address-family ipv4 unicast
  network 192.168.0.0 mask 255.255.255.0
  neighbor 10.0.0.2 activate
  neighbor 10.0.0.2 route-map ALLOW-ALL out
```

### Modern Routing Concepts

- **Anycast**: Same IP from multiple locations (DNS, CDN, DDoS mitigation)
- **BGP communities**: Tags for policy enforcement
- **Route reflection / Confederation**: Scalable iBGP
- **BGPsec / RPKI**: Origin validation, route hijacking prevention

---

## 2.5 Switching & Data Center Fabrics

### Traditional 3-Tier DC Architecture

```
            ┌─────────────────┐
            │   INTERNET      │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │  CORE LAYER     │  ← L3, fast forwarding, NAT
            │  (2 routers)    │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │  AGGREGATION    │  ← L3/L2 boundary, ACLs, QoS
            │  (Modular DCs)  │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │  ACCESS LAYER   │  ← L2, port security, PoE
            │  (ToR switches) │
            └─────────────────┘
```

### Modern Spine-Leaf Architecture

```
                          Spine Layer
                  S1      S2      S3      S4
                 /|\\    /|\\    /|\\    /|\\
                / | \\  / | \\  / | \\  / | \\
               /  |  \\/  |  \\/  |  \\/  |  \\
              /   |  /\\  |  /\\  |  /\\  |  \\
             /    | /  \\ | /  \\ | /  \\ | /  \\
            L1    L2    L3    L4    L5    L6    L7    L8
                          Leaf Layer

  • Every leaf connects to EVERY spine (full bipartite)
  • ECMP load-balancing across all paths
  • Predictable latency (≤ 2 hops)
  • Easy scale: add spines (east-west bandwidth) or leaves (ports)
```

| Property | Spine-Leaf | 3-Tier |
|----------|-----------|--------|
| Hops | 2 (predictable) | 3-4 |
| East-West BW | High (ECMP) | Limited (oversubscription) |
| Scalability | Linear | Layered |
| Failure domain | Isolated | Larger |
| Oversubscription | 1:1 typical | 4:1+ typical |

### Overlay Networking — VXLAN & EVPN

```
┌──────────────────────────────────────────────────────────┐
│                  VXLAN EVPN                              │
├──────────────────────────────────────────────────────────┤
│  Original L2 Frame                                       │
│   └─ VXLAN Header (24-bit VNI = 16M segments)            │
│      └─ UDP Header (Dst Port 4789)                       │
│         └─ Outer IP Header (Underlay L3)                 │
│            └─ Outer Ethernet Header (Underlay L2)        │
└──────────────────────────────────────────────────────────┘

Benefits:
• L2 over L3 underlay (routable)
• 16M logical segments (vs 4094 VLANs)
• Multi-tenancy
• Works across data centers (DCI)
```

### Network Virtualization Stack

```
┌─────────────────────────────────────────────┐
│  Application Workload (VM/Container/Pod)   │
├─────────────────────────────────────────────┤
│  Hypervisor / Container Runtime             │
├─────────────────────────────────────────────┤
│  Virtual Switch (vSwitch, OVS, CNI plugin) │
├─────────────────────────────────────────────┤
│  Overlay Network (VXLAN, Geneve, IPsec)    │
├─────────────────────────────────────────────┤
│  Underlay Physical Network (Spine-Leaf)    │
├─────────────────────────────────────────────┤
│  Cabling / Optics / Transceivers            │
└─────────────────────────────────────────────┘
```

---

## 2.6 Transport Layer Deep Dive

### TCP/IP State Machine

```
        ┌─────────┐    SYN     ┌──────────┐
        │  CLOSED │ ─────────▶ │ SYN-SENT │
        └─────────┘            └─────┬────┘
              ▲                      │ SYN+ACK
              │ FIN                  ▼
        ┌─────┴────┐            ┌──────────┐
        │ TIME-WAIT│ ◀──FIN+ACK │ESTABLISHED│
        └─────────┘            └──────────┘
              ▲                      ▲
              │ FIN                  │ ACK
              │                      │
        ┌─────┴────┐            ┌────┴─────┐
        │ CLOSE-WAIT│ ◀──FIN    │FIN-WAIT-1│
        └──────────┘            └──────────┘

3-Way Handshake: SYN → SYN+ACK → ACK
4-Way Termination: FIN → ACK → FIN → ACK (TIME-WAIT = 2*MSL = ~60s)
```

### TCP Performance Tuning

```bash
# Linux TCP buffers (auto-tuning since 2.6)
net.ipv4.tcp_rmem = 4096 87380 6291456
net.ipv4.tcp_wmem = 4096 65536 6291456
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728

# Congestion control
sysctl net.ipv4.tcp_congestion_control = bbr  # BBR for high BW × latency
sysctl net.ipv4.tcp_ecn = 1                    # Explicit Congestion Notification

# Connection limits
sysctl net.ipv4.tcp_max_syn_backlog = 65535
sysctl net.core.somaxconn = 65535
sysctl net.ipv4.tcp_tw_reuse = 1
sysctl net.ipv4.tcp_fin_timeout = 15

# TCP Fast Open (TFO) — send data in SYN packet
sysctl net.ipv4.tcp_fastopen = 3

# TCP window scaling for high BDP
sysctl net.ipv4.tcp_window_scaling = 1
sysctl net.ipv4.tcp_sack = 1
sysctl net.ipv4.tcp_timestamps = 1
```

### UDP & QUIC

```
┌─────────────────────────────────────────────────────────────┐
│                       UDP Use Cases                          │
├─────────────────────────────────────────────────────────────┤
│  • DNS (53), NTP (123), SNMP (161/162)                      │
│  • VoIP, video conferencing (RTP/RTCP)                      │
│  • Online gaming (low latency, packet loss tolerant)         │
│  • IoT telemetry (small messages, high frequency)            │
│  • QUIC (HTTP/3) — UDP-based reliable transport             │
└─────────────────────────────────────────────────────────────┘

QUIC Advantages over TCP+TLS:
┌─────────────────────────────────────────────────────────────┐
│  ✓ 0-RTT / 1-RTT handshake (vs 2-RTT TCP+TLS)               │
│  ✓ Built-in encryption (always TLS 1.3+)                    │
│  ✓ Multiplexed streams (no head-of-line blocking)            │
│  ✓ Connection migration (WiFi ↔ LTE)                         │
│  ✓ Better loss recovery & congestion control                 │
└─────────────────────────────────────────────────────────────┘
```

### TCP Troubleshooting Flow

```bash
# Step 1: Can I reach the host?
ping <ip>
traceroute <ip>           # Linux
tracert <ip>              # Windows
mtr <ip>                  # Combined ping+traceroute

# Step 2: Is the port open?
nc -zv <host> <port>      # Quick test
nmap -p 1-65535 <host>    # Port scan

# Step 3: TCP handshake analysis
tcpdump -i any -nn -vv host <ip> and port <port>
ss -tnp dst <ip>:<port>   # Socket state
netstat -an | grep <port>

# Step 4: Performance analysis
iperf3 -c <server>                    # Bandwidth test
iperf3 -c <server> -t 30 -P 4         # Parallel streams
mtr -T -P <port> <ip>                 # TCP-aware traceroute

# Step 5: Packet capture for deep analysis
tcpdump -i eth0 -w capture.pcap port 443
# Then open in Wireshark, analyze:
#   - TCP retransmissions
#   - Window size (zero window = backpressure)
#   - RTT, jitter
#   - TLS handshake timing
```

---

## 2.7 DNS — The Phonebook of the Internet

### DNS Hierarchy & Resolution

```
                Root (.)
                  │
        ┌─────────┼─────────┐
        │         │         │
       .com     .org     .net
        │         │         │
   ┌────┼────┐    │    ┌────┴────┐
 google  aws  fb  wikipedia   cloudflare
   │      │    │       │           │
 www   api   mail   en         api
```

### Record Types

| Type | Purpose | Example |
|------|---------|---------|
| **A** | IPv4 address | `www.example.com → 93.184.216.34` |
| **AAAA** | IPv6 address | `www.example.com → 2606:2800:220:1:248:1893:25c8:1946` |
| **CNAME** | Alias | `www → example.com` |
| **MX** | Mail server | `example.com → 10 mail.example.com` |
| **NS** | Name servers | `example.com → ns1.example.com` |
| **TXT** | Verification, SPF, DKIM | `google-site-verification=...` |
| **SRV** | Service location | `_sip._tcp.example.com` |
| **CAA** | CA authorization | `0 issue "letsencrypt.org"` |
| **PTR** | Reverse DNS | `34.216.184.93.in-addr.arpa` |
| **DS/DNSKEY** | DNSSEC chain of trust | — |

### DNS Resolution Flow

```
Client → Recursive Resolver (e.g., 8.8.8.8)
         │
         ├──▶ Root NS (.) → "ask .com NS"
         │        │
         ├──▶ TLD NS (.com) → "ask example.com NS"
         │        │
         ├──▶ Authoritative NS (example.com) → "A record: 93.184.216.34"
         │        │
         └──▶ Client receives answer (cached for TTL)
```

### DNS Performance & Reliability

```yaml
# Strategy: Multi-vendor + Short TTL for critical services
ns1.example.com     # Primary (e.g., AWS Route 53)
ns2.example.com     # Secondary (e.g., Cloudflare)
ns3.example.com     # Tertiary (e.g., Akamai)

# TTL strategy
Static records (web):    3600s   (1 hour)
Critical/failover (DB):  60s     (fast failover)
Mail (MX):               86400s  (24 hours)

# Health checks + failover
Route 53 Health Check → Auto DNS failover
Health check endpoints: /health, /healthz, /ready
```

### Modern DNS Features

- **DNS over HTTPS (DoH)**: `https://dns.cloudflare.com/dns-query`
- **DNS over TLS (DoT)**: Port 853
- **DNSSEC**: Cryptographic validation chain
- **ECS (EDNS Client Subnet)**: Better CDN routing
- **Service Discovery**: Consul, etcd, CoreDNS

---

## 2.8 Load Balancing & Traffic Management

> *Detailed coverage in Chapter 8 — here's the network-layer perspective*

### L4 vs L7 Load Balancing

```
┌────────────────────────────────────────────────────────────────┐
│                        L4 LB                                   │
│  • TCP/UDP level                                              │
│  • Faster (no payload parsing)                                │
│  • No SSL termination (passthrough) or separate SSL LB        │
│  • Examples: AWS NLB, IPVS, HAProxy TCP mode                  │
├────────────────────────────────────────────────────────────────┤
│                        L7 LB                                   │
│  • HTTP/gRPC level                                            │
│  • Content-based routing, header manipulation                 │
│  • TLS termination, WAF integration                           │
│  • Examples: NGINX, Envoy, HAProxy HTTP mode, AWS ALB         │
└────────────────────────────────────────────────────────────────┘
```

### Anycast for DDoS Mitigation

```
Same IP announced from multiple PoPs:
  192.0.2.1 → AS65000 (NY)
  192.0.2.1 → AS65000 (LA)
  192.0.2.1 → AS65000 (LDN)
  
BGP routes traffic to nearest/best path
DDoS traffic distributed across PoPs
```

---

## 2.9 Network Security

### Defense-in-Depth Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 7: WAF (SQLi, XSS, CSRF protection)                 │
│  Layer 6: TLS (encryption in transit)                      │
│  Layer 5: IDS/IPS (anomaly detection)                      │
│  Layer 4: Firewall (stateful, L4 rules)                    │
│  Layer 3: Router ACLs, BGP filters, RPKI                   │
│  Layer 2: Port security, DHCP snooping, DAI                │
│  Layer 1: Physical security, cable management              │
└─────────────────────────────────────────────────────────────┘
```

### Zero-Trust Network (BeyondCorp)

```
Traditional Network Model:
┌─────────────────────────────────────┐
│  Inside = Trusted, Outside = Enemy  │  ← Perimeter-based
└─────────────────────────────────────┘

Zero-Trust Model:
┌─────────────────────────────────────────────────────────────┐
│  Trust NOTHING, Verify EVERY request                         │
│  • Identity-based (user + device + context)                  │
│  • mTLS between services                                    │
│  • Least privilege (just-in-time access)                    │
│  • Continuous verification                                   │
│  • Microsegmentation                                        │
│  • BeyondCorp (Google), BeyondCorp Enterprise                │
└─────────────────────────────────────────────────────────────┘

Technologies:
• SPIFFE/SPIRE (workload identity)
• Istio/Linkerd (service mesh with mTLS)
• Cloudflare Access, Zscaler ZIA, Tailscale
• WireGuard (modern VPN)
```

### Segmentation Examples

```
┌─────────────────────────────────────────────────────────────┐
│              Network Segmentation Strategy                    │
├─────────────────────────────────────────────────────────────┤
│  VLAN 10 — Management (OOB, iLO, switches)                   │
│  VLAN 20 — Servers - Web Tier                                │
│  VLAN 30 — Servers - App Tier                                │
│  VLAN 40 — Servers - DB Tier                                 │
│  VLAN 50 — DMZ (public-facing)                               │
│  VLAN 60 — User Devices                                      │
│  VLAN 70 — IoT / Printers / BYOD                             │
│  VLAN 80 — Voice (QoS priority)                              │
│  VLAN 90 — Guest WiFi (internet only)                        │
├─────────────────────────────────────────────────────────────┤
│  Firewall Rules:                                             │
│    VLAN 50 → VLAN 20: ALLOW 80/443                           │
│    VLAN 20 → VLAN 30: ALLOW 8080-8090                        │
│    VLAN 30 → VLAN 40: ALLOW 5432 (PostgreSQL)                │
│    VLAN 40 → ALL: DENY (no egress from DB)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2.10 TLS 1.3 — Modern Transport Security

### TLS 1.2 vs 1.3 Handshake

```
TLS 1.2 (2-RTT):
  Client → Server: ClientHello
  Server → Client: ServerHello, Certificate, ServerKeyExchange, ServerHelloDone
  Client → Server: ClientKeyExchange, ChangeCipherSpec, Finished
  Server → Client: ChangeCipherSpec, Finished
  [Application Data]

TLS 1.3 (1-RTT, optional 0-RTT):
  Client → Server: ClientHello + KeyShare
  Server → Client: ServerHello + KeyShare + {EncryptedExtensions, Cert, Verify}
  Client → Server: {Finished}
  [Application Data]
  
  0-RTT replay: ClientHello + KeyShare + 0-RTT Data
                ⚠ Idempotent only, replay risk
```

### Cipher Suite Selection (TLS 1.3)

```
TLS_AES_256_GCM_SHA384         ← Strongest, slower
TLS_CHACHA20_POLY1305_SHA256   ← ARM/mobile optimized
TLS_AES_128_GCM_SHA256         ← Balanced (recommended default)
TLS_AES_128_CCM_SHA256         ← Constrained devices

Removed from TLS 1.3:
✗ RC4, DES, 3DES, MD5, SHA-1
✗ Static RSA (no forward secrecy)
✗ CBC mode ciphers (BEAST, POODLE)
✗ Compression (CRIME attack)
```

### mTLS for Service-to-Service

```
Service A                          Service B
   │                                  │
   ├─── ClientHello ────────────────▶ │
   ├─── ServerHello + Cert ─────────▶ │
   │    (B presents its cert)         │
   ├─── ClientCert ─────────────────▶ │
   │    (A presents its cert)         │
   │    (mutual verification)         │
   ├─── Finished ───────────────────▶ │
   │                                  │
   └─── Encrypted Application Data ──▶│

SPIFFE ID Format:
  spiffe://trust-domain/path/workload-id
  Example: spiffe://prod.example.com/ns/default/sa/api-server

Implementation:
  • Istio (automatic mTLS)
  • Linkerd (automatic mTLS)
  • Consul Connect
  • Cert-manager + SPIRE
```

---

## 2.11 Software-Defined Networking (SDN)

### SDN Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   SDN ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────┤
│  Application Layer (Northbound API)                         │
│       │                                                     │
│  Control Layer (SDN Controller: OpenDaylight, ONOS,         │
│                 Cisco ACI, VMware NSX, Akanda)              │
│       │                                                     │
│  Infrastructure Layer (Switches, Routers — OpenFlow)        │
│                                                             │
│  Southbound API: OpenFlow, NETCONF, gNMI, gNOI              │
└─────────────────────────────────────────────────────────────┘
```

### Network Automation & Observability

```bash
# Ansible network modules
ansible-playbook -i inventory router-config.yml
  # cisco.ios.ios_command, cisco.ios.ios_config
  # arista.eos.eos_config, junipernetworks.junos.junos_config

# NETCONF example (Cisco IOS-XE)
<rpc message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <get-config>
    <source><running/></source>
    <filter>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"/>
    </filter>
  </get-config>
</rpc>

# gNMI (gRPC Network Management Interface) — modern streaming telemetry
gnmi_get -target 10.0.0.1 -port 57400 \
  -xpath /interfaces/interface[name=eth0]/state/counters

# Streaming telemetry (real-time, push-based vs SNMP polling)
# YANG models define the data schema
# OpenConfig, IETF YANG modules
```

---

## 2.12 Network Tools & Troubleshooting

### Essential Toolbelt

| Tool | Purpose | Example |
|------|---------|---------|
| **ping** | Reachability, RTT | `ping -c 5 8.8.8.8` |
| **traceroute/mtr** | Path discovery | `mtr -rwc 30 8.8.8.8` |
| **tcpdump** | Packet capture | `tcpdump -i eth0 -nn -w cap.pcap` |
| **Wireshark** | GUI packet analysis | Open cap.pcap |
| **iperf3** | Bandwidth test | `iperf3 -c server -P 4 -t 60` |
| **netstat/ss** | Socket state | `ss -tnp state established` |
| **nmap** | Port scan, fingerprint | `nmap -sV -p- host` |
| **dig/nslookup** | DNS queries | `dig +trace example.com` |
| **curl** | HTTP testing | `curl -vLk https://example.com` |
| **httping** | HTTP latency | `httping -g https://example.com` |
| **iperf3/nuttcp** | Network throughput | — |
| **ethtool** | NIC/driver stats | `ethtool -S eth0` |
| **ip / ifconfig** | Interface config | `ip addr show` |
| **tcpdump** | Capture | `tcpdump -i any port 443` |
| **bmon/nload** | Live bandwidth | — |
| **nethogs** | Per-process bandwidth | — |

### Wireshark Display Filters (Go-To List)

```
ip.addr == 10.0.0.1
ip.src == 10.0.0.1 && ip.dst == 10.0.0.2
tcp.port == 443
tcp.flags.syn == 1
tcp.analysis.retransmission
http.request.method == "POST"
dns.qry.name == "example.com"
tls.handshake.type == 1
follow tcp stream: right-click → Follow → TCP Stream
```

---

## 2.13 Network Design Patterns

### Multi-Region Active-Active

```
┌──────────────────┐         ┌──────────────────┐
│   US-EAST-1      │         │   EU-WEST-1      │
│ ┌──────────────┐ │         │ ┌──────────────┐ │
│ │ Edge LB      │ │         │ │ Edge LB      │ │
│ ├──────────────┤ │         │ ├──────────────┤ │
│ │ App Cluster  │ │◄───────►│ │ App Cluster  │ │
│ ├──────────────┤ │  DWDM   │ ├──────────────┤ │
│ │ DB Primary   │ │  or     │ │ DB Standby   │ │
│ └──────────────┘ │  IPsec  │ └──────────────┘ │
└──────────────────┘         └──────────────────┘
         │                              │
         └──────────────┬───────────────┘
                        ▼
                ┌──────────────┐
                │ Global DNS  │
                │ (Route 53,  │
                │  Cloudflare)│
                └──────────────┘

Geolocation/Geoproximity routing → nearest region
Cross-region replication for data
Async event replication between regions
```

### Hybrid Cloud Connectivity

```
┌─────────────────────────────────────────────────────────────┐
│         Connectivity Options Comparison                       │
├─────────────────────────────────────────────────────────────┤
│ Method       Bandwidth    Latency    Cost      Use Case     │
├─────────────┼────────────┼───────────┼─────────┼─────────────┤
│ Internet IPsec│ ~1 Gbps   │ 20-80ms  │ Low     │ Small/Med  │
│ AWS DX/GCP IC│ 1-100Gbps │ <5ms     │ High    │ Heavy BW   │
│ SD-WAN       │ Variable  │ Variable │ Medium  │ Multi-site │
│ MPLS         │ Variable  │ Low      │ High    │ Enterprise │
│ ZeroTier/Tail│ Varies    │ Internet │ Low     │ Modern VPN │
└─────────────────────────────────────────────────────────────┘
```

---

## 2.14 Exercises

### Exercise 1: Subnet Design
You have `10.0.0.0/16`. Design subnets for:
- Management (need 100 hosts)
- Web Tier (need 500 hosts)
- App Tier (need 500 hosts)
- DB Tier (need 250 hosts)
- Point-to-point links (need 2 hosts each, 5 links)

Provide subnets in CIDR with first usable host, last usable host, broadcast.

### Exercise 2: BGP Path Selection
Given these BGP routes to `203.0.113.0/24`:
- Route A: AS_PATH [65001 65002], LOCAL_PREF 100, MED 50
- Route B: AS_PATH [65001 65003 65002], LOCAL_PREF 200, MED 100
- Route C: AS_PATH [65004 65002], LOCAL_PREF 100, MED 50

Which wins? Walk through the decision tree.

### Exercise 3: TCP Analysis
You see 15% packet loss on a long-distance TCP connection. Using BBR vs Cubic, what's the expected throughput? Calculate using Mathis formula:
`B = (MSS / RTT) * (1 / sqrt(p))`
- MSS = 1460 bytes
- RTT = 100ms
- p (loss rate) = 0.15

### Exercise 4: TLS 1.3 Migration
You're migrating 200 microservices from TLS 1.2 to TLS 1.3 with mTLS. Write an Architecture Decision Record covering:
- Why migrate (security, performance)
- Rollout strategy (canary, phased)
- Risks (compatibility, cert rotation)
- Rollback plan

### Exercise 5: Troubleshooting Scenario
A user reports: "Sometimes my connection to `api.example.com` takes 10s, sometimes 100ms." 
- Walk through your investigation steps
- What data would you collect?
- List 5 possible root causes with remediation

---

## 2.15 Further Reading

### Books
- *Computer Networking: A Top-Down Approach* — Kurose & Ross
- *TCP/IP Illustrated, Vol. 1* — W. Richard Stevens
- *Network Warrior* — Gary A. Donahue
- *BGP* — Iljitsch van Beijnum
- *Site Reliability Engineering* — Google (Ch. 6, 13)

### Standards & RFCs
- **RFC 793** — TCP
- **RFC 8200** — IPv6
- **RFC 8446** — TLS 1.3
- **RFC 9000** — QUIC
- **RFC 4271** — BGP-4
- **RFC 2328** — OSPF v2

### Online Resources
- [Cloudflare Learning Center](https://www.cloudflare.com/learning/)
- [Julio Biason Blog](https://blog.juliobiason.net/) — Networking deep-dives
- [Packet Pushers Podcast](https://packetpushers.net/)
- [Wireshark Official Docs](https://www.wireshark.org/docs/)

### YouTube Channels
- **NetworkChuck** — Beginner-friendly, hands-on
- **David Bombal** — Cisco/CCNP-level labs
- **Ben Eater** — Low-level networking (building a router from scratch)

---

## 2.16 Summary Checklist

- [ ] Can explain OSI vs TCP/IP models with examples
- [ ] Can subnet a /16 in my head
- [ ] Understand IPv6 address types and transition mechanisms
- [ ] Can configure OSPF/BGP on a Cisco/Juniper/FRR router
- [ ] Can design a spine-leaf fabric for 10K servers
- [ ] Can troubleshoot TCP issues with tcpdump + Wireshark
- [ ] Understand TLS 1.3 handshake and cipher suites
- [ ] Can design DNS architecture with failover
- [ ] Know when to use anycast vs unicast
- [ ] Can articulate zero-trust vs perimeter security models
- [ ] Comfortable with iperf3, mtr, dig, ss for diagnostics

---

> **Next Chapter**: [Chapter 3: Distributed Systems Concepts](../chapters/03-distributed-systems-concepts.md) — Consensus, consistency models, and the building blocks of distributed systems.