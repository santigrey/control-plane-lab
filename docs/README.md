# Home AI Platform (3-Node Lab)

## Topology

- **sloan3 (Cisco Kid)** — Control Plane / Memory / Orchestration  
- **sloan2 (The Beast)** — GPU / Models / Inference (future)  
- **sloan1 (Slim Jim)** — Devices / Bots / Edge (Wire-Pod)

## sloan3 (Cisco Kid) — Baseline

### OS & Hardware
- Ubuntu 22.04 LTS (jammy)
- Cisco UCS C240 (M4)
- Static IP: `192.168.1.10`

### Storage (LVM)
- Root filesystem: ~100 GB (kept small and stable)
- Dedicated Docker data volume:
  - LV: `docker-lv` (500 GB)
  - Mounted at: `/var/lib/docker`

### Container Runtime
- Docker Engine (official Docker repository)
- Verified non-root Docker access for operator user

### Observability
- Netdata agent running
- Dashboard: `http://192.168.1.10:19999`

### Control-Plane Services
#### PostgreSQL (metadata/state DB)
- Compose location: `~/control-plane/postgres/compose.yaml`
- Container: `control-postgres`
- Port: `5432`
- DB: `controlplane`

**Why PostgreSQL first:** establishes a production-standard “state spine” for orchestration, agent state, job metadata, and future AI services.

---

## Design Rationale (Interview Framing)

This platform is intentionally split into **control, compute, and edge roles** to mirror real production AI systems.

- The **control plane (Cisco Kid)** is optimized for reliability, state, and observability rather than raw compute.
- Core services (Docker, PostgreSQL, Netdata) are isolated from GPU workloads to prevent resource contention.
- LVM-backed storage allows safe growth, predictable performance, and clean separation of concerns.

This design enables:
- safer iteration on AI services
- clearer failure domains
- production-style debugging and monitoring
- realistic system design discussions in interviews

The lab is operated incrementally: baseline → verify → document → extend.
