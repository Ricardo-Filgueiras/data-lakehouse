# Habilitando Autenticação por Senha no Trino

Este guia descreve o processo completo para habilitar autenticação por usuário e senha no Trino utilizando **Password File Authentication**.

---

## Visão Geral

Por padrão, o Trino não permite autenticação por senha. Para habilitar esse recurso é necessário:

1. Ativar HTTPS (obrigatório)
2. Configurar o tipo de autenticação como `PASSWORD`
3. Criar um arquivo de usuários com senha criptografada
4. Configurar o password authenticator
5. Reiniciar o serviço

---

# 1. Habilitar HTTPS (Obrigatório)

Edite o arquivo:

```
etc/config.properties
```

Adicione:

```properties
http-server.https.enabled=true
http-server.https.port=8443
http-server.https.keystore.path=/etc/trino/keystore.jks
http-server.https.keystore.key=SENHA_DO_KEYSTORE
```

### Observações

* A autenticação por senha não funciona sem HTTPS.
* O keystore pode ser gerado com `keytool`.

Exemplo de geração de keystore:

```bash
keytool -genkeypair \
  -alias trino \
  -keyalg RSA \
  -keystore /etc/trino/keystore.jks
```

---

# 2. Habilitar Autenticação por Senha

No mesmo arquivo `config.properties`, adicione:

```properties
http-server.authentication.type=PASSWORD
```

---

# 3. Criar Arquivo de Usuários

Crie o arquivo:

```
/etc/trino/password.db
```

As senhas devem estar no formato bcrypt.

### Gerar usuário com htpasswd

```bash
htpasswd -B -c /etc/trino/password.db usuario
```

Para adicionar novos usuários:

```bash
htpasswd -B /etc/trino/password.db outro_usuario
```

---

# 4. Configurar Password Authenticator

Crie o arquivo:

```
etc/password-authenticator.properties
```

Conteúdo:

```properties
password-authenticator.name=file
file.password-file=/etc/trino/password.db
```

---

# 5. Reiniciar o Trino

```bash
systemctl restart trino
```

Ou, se estiver usando Docker:

```bash
docker restart trino
```

---

# Validação

Acesse:

```
https://SEU_HOST:8443
```

O sistema deverá solicitar usuário e senha.

---

# Checklist de Verificação

* [ ] HTTPS habilitado
* [ ] Keystore configurado corretamente
* [ ] authentication.type configurado como PASSWORD
* [ ] password.db criado com bcrypt
* [ ] password-authenticator.properties criado
* [ ] Serviço reiniciado

---

# Considerações de Segurança

* Nunca utilize autenticação por senha sem HTTPS.
* Restrinja permissões do arquivo `password.db`.
* Em ambientes corporativos, considere LDAP ou OAuth2.

---

## Estrutura Final Esperada

```
etc/
 ├── config.properties
 ├── password-authenticator.properties
 └── password.db
```

---

Documento pronto para uso em ambiente local, servidor dedicado ou containerizado.
