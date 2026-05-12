# 🛠️ Scripts de Mantenimiento — ERP Nexus

##docker-compose exec -T db vacuumdb -U erp erp_nexus --verbose --analyze
```

### **Restore** (`scripts/restore-db.sh`)
```bash
# Restaurar desde backup específico
./scripts/restore-db.sh daily/erp_nexus_20260511_120000.sql.gz

# Restaurar el backup más reciente
./scripts/restore-db.sh latest
```
> **Nota:** El restore detiene temporalmente el contenedor `web` para consistencia.

### **PostgreSQL Maintenance** (`scripts/maintenance-db.sh`)
```bash
./scripts/maintenance-db.sh
```
Muestra: conexiones activas, tamaño DB, top queries lentas, cache hit ratio.

### **Redis Maintenance** (`scripts/maintenance-redis.sh`)
```bash
./scripts/maintenance-redis.sh
```
Muestra: stats, memoria, keyspace, slowlog, persistencia.

---

## ⚙️ Configuración Avanzada

### Variables de Entorno
Los scripts respetan:
- `POSTGRES_USER` — usuario DB (default: `erp`)
- `POSTGRES_DB` — nombre DB (default: `erp_nexus`)
- `REDIS_PASSWORD` — contraseña Redis

Asegúrate de que `.env.prod` tenga estos valores.

### Volúmenes
- `/backup` — montado en `docker-compose.prod.yml` para almacenar backups
- `pgdata` — datos PostgreSQL (persistente)
- `redisdata` — datos Redis con AOF persistente

---

## 🔄 Automatización (cron)

Agregar a cron (dentro del host o contenedor de backup):

```cron
# Backup diario a las 02:00 AM
0 2 * * * cd /ruta/erp-nexus && ./scripts/backup-db.sh >> /var/log/erp-backup.log 2>&1
```

Para rotación externa (ej: copiar backups a S3 o servidor remoto), puedes extender `backup-db.sh` con `aws s3 cp`.

---

## 🚨 Troubleshooting

| Error | Solución |
|-------|----------|
| `pg_dump: connection to database failed` | Verificar `POSTGRES_PASSWORD` y que contenedor `db` esté healthy |
| `permission denied on /backup` | Asegurar volumen `backup` montado y con permisos `erp:erp` |
| `pg_stat_statements extension not found` | Usar `postgres:16` (no-alpine) o instalar `postgresql-contrib` |
| `redis-cli: Authentication required` | Configurar `REDIS_PASSWORD` en `.env.prod` |

---

## 📚 Referencias

- [PostgreSQL Tuning](https://pgtune.leopard.in.ua/)
- [Redis Persistence](https://redis.io/docs/management/persistence/)
- [Docker Compose Volumes](https://docs.docker.com/compose/compose-file/compose-file-v3/#volumes)
