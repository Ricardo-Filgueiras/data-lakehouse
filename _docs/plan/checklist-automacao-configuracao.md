# Checklist: Automação e Configuração do Ambiente

## 1. Padronizar arquivos de configuração
- [ ] Criar arquivos `.env` para cada serviço (Airflow, Trino, MinIO, etc.)
- [ ] Adicionar `.env` ao `.gitignore` para evitar exposição de segredos

## 2. Revisar e modularizar Docker Compose
- [ ] Garantir que cada serviço tem seu próprio `docker-compose.yml` (ex: airflow/docker-compose.yml, trino/docker-compose.yml)
- [ ] Verificar se todos os serviços leem variáveis do `.env` correspondente
- [ ] Criar `.env.example` para cada serviço, documentando variáveis obrigatórias

## 3. Criar scripts de inicialização
- [ ] Desenvolver script principal (`start.sh` ou `start.ps1`) na raiz do projeto
- [ ] Validar existência dos arquivos `.env` necessários no script
- [ ] Automatizar criação da rede Docker se não existir
- [ ] Subir os serviços na ordem correta (Trino/MinIO, depois Airflow)
- [ ] Exibir mensagens de status e instruções pós-provisionamento

## 4. Automatizar criação de buckets, bancos e estruturas iniciais
- [ ] Incluir comandos no script para criar buckets no MinIO (se necessário)
- [ ] Automatizar inicialização de bancos/metastore
- [ ] Validar saúde dos serviços após o start

## 5. Versionar arquivos de configuração e exemplos
- [ ] Adicionar `.env.example` e exemplos de configuração ao repositório
- [ ] Documentar no README como copiar e personalizar os arquivos `.env`

## 6. Documentar o processo
- [ ] Atualizar o README com instruções claras de setup, dependências e troubleshooting
- [ ] Incluir fluxograma ou checklist do processo de provisionamento

## 7. Verificação final
- [ ] Executar o script principal em ambiente limpo e validar funcionamento dos serviços
- [ ] Garantir que variáveis sensíveis não estão versionadas
- [ ] Validar cobertura da documentação para todos os passos e possíveis erros
- [ ] Testar reprodutibilidade em outra máquina ou ambiente
