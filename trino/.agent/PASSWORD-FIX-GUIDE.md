# Correção da Autenticação por Senha no Trino (Windows + Docker Desktop)

Este guia descreve o passo a passo para corrigir o erro causado por:

```
http-server.authentication.type=PASSWORD
```

com HTTPS desabilitado.

No Trino, autenticação por senha exige HTTPS obrigatoriamente.

---

# Visão Geral da Correção

Você irá:

1. Gerar um keystore (TLS)
2. Ajustar o `config.properties`
3. Atualizar o `docker-compose.yml`
4. Reiniciar o ambiente
5. Validar o acesso

Ambiente considerado:

* Windows
* Docker Desktop
* Projeto com pasta `conf/`

---

# 1. Gerar Keystore no Windows

O Java já inclui a ferramenta `keytool`.

No PowerShell, execute dentro da pasta `conf`:

```powershell
keytool -genkeypair `
  -alias trino `
  -keyalg RSA `
  -keystore keystore.jks `
  -storepass changeit `
  -keypass changeit `
  -dname "CN=localhost" 
```

Isso criará:

```
conf/keystore.jks
```

Para desenvolvimento local, usar `localhost` é suficiente.

---

# 2. Ajustar config.properties

Substitua o conteúdo relacionado a HTTP/HTTPS por:

```properties
coordinator=true
node-scheduler.include-coordinator=true

# Desabilitar HTTP
http-server.http.enabled=false

# Habilitar HTTPS
http-server.https.enabled=true
http-server.https.port=8443
http-server.https.keystore.path=/etc/trino/keystore.jks
http-server.https.keystore.key=changeit

# Autenticação por senha
http-server.authentication.type=PASSWORD

discovery-server.enabled=true
discovery.uri=https://trino:8443
```

Observações importantes:

* A senha do keystore deve ser igual à usada na geração.
* A URI de discovery deve usar HTTPS e a porta 8443.

---

# 3. Atualizar docker-compose.yml

Atualize a seção do serviço `trino`:

```yaml
services:
  trino:
    image: trinodb/trino:405
    container_name: trino
    hostname: trino
    ports:
      - 8443:8443
    volumes:
      - ./conf/config.properties:/etc/trino/config.properties
      - ./conf/password.db:/etc/trino/password.db
      - ./conf/password-authenticator.properties:/etc/trino/password-authenticator.properties
      - ./conf/keystore.jks:/etc/trino/keystore.jks
      - ./conf/hive.properties:/etc/trino/catalog/hive.properties
      - ./conf/delta.properties:/etc/trino/catalog/delta.properties
      - ./conf/iceberg.properties:/etc/trino/catalog/iceberg.properties
      - ./conf/postgres.properties:/etc/trino/catalog/postgres.properties
      - ./conf/sqlserver.properties:/etc/trino/catalog/sqlserver.properties
```

Mudanças aplicadas:

* Porta alterada para 8443
* Keystore montado dentro do container
* HTTP removido

---

# 4. Validar password.db

O arquivo deve conter linhas no formato:

```
usuario:$2y$hash_bcrypt
```

Se ainda não criou:

No Windows, use Git Bash ou WSL:

```bash
htpasswd -B -c password.db admin
```

Ou gere online bcrypt e cole manualmente.

---

# 5. Reiniciar Ambiente

No PowerShell:

```powershell
docker compose down
docker compose up -d
```

Verificar logs:

```powershell
docker logs -f trino
```

O servidor deve iniciar sem erro de Guice.

---

# 6. Acessar Trino

Abra no navegador:

```
https://localhost:8443
```

O navegador exibirá aviso de certificado (esperado em ambiente local).

Aceite o risco e prossiga.

O login deverá solicitar usuário e senha.

---

# Checklist Final

* [ ] keystore.jks criado
* [ ] HTTPS habilitado
* [ ] HTTP desabilitado
* [ ] Porta 8443 exposta
* [ ] Keystore montado no container
* [ ] password.db válido
* [ ] Serviço reiniciado

---

# Problemas Comuns

### 1. Porta já em uso

Verifique se 8443 não está ocupada.

### 2. Keystore não encontrado

Confirme que o volume está correto.

### 3. Senha incorreta do keystore

Deve coincidir com `http-server.https.keystore.key`.

---

# Resultado Esperado

* Trino inicia corretamente
* Login por usuário/senha funcional
* Ambiente seguro mesmo em desenvolvimento

---

Guia validado para Windows + Docker Desktop.
