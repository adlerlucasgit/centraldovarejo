# Central do Varejo

Sistema de gerenciamento de produtos, estoque e vendas desenvolvido como projeto acadêmico de Engenharia de Software.

## Tecnologias utilizadas

- Python 3.14.8
- Django 6.1.1
- SQLite
- Django ORM
- HTML5 e CSS3
- Bootstrap 5.3.3
- Bootstrap Icons
- JavaScript
- Git

## Funcionalidades

- Autenticação de usuários.
- Gerenciamento de usuários e permissões.
- Cadastro, edição, consulta e desativação de produtos.
- Consulta e controle de estoque.
- Registro de entradas e ajustes de estoque.
- Registro e finalização de vendas.
- Atualização automática do estoque após uma venda.
- Histórico de vendas com filtros e detalhes.
- Dashboard com indicadores operacionais.
- Relatórios gerenciais.

## Perfis de acesso

### Administrador

Possui acesso às funcionalidades administrativas do sistema:

- Gerenciar produtos.
- Registrar entradas e ajustes de estoque.
- Consultar todas as vendas.
- Gerenciar usuários.
- Consultar relatórios.
- Acessar o dashboard.

### Caixa

Possui acesso às operações de atendimento:

- Consultar produtos.
- Consultar estoque.
- Registrar e finalizar vendas.
- Consultar o próprio histórico de vendas.
- Acessar o dashboard.

## Requisitos para execução

- Python instalado.
- Git instalado.
- PowerShell ou terminal compatível.

## Instalação

### 1. Clonar o repositório

```powershell
git clone https://github.com/adlerlucasgit/centraldovarejo.git
```

Entre na pasta do projeto:

```powershell
cd centraldovarejo
```

### 2. Criar o ambiente virtual

```powershell
python -m venv .venv
```

### 3. Ativar o ambiente virtual

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Instalar as dependências

```powershell
python -m pip install -r requirements.txt
```

### 5. Aplicar as migrations

```powershell
python manage.py migrate
```

### 6. Criar o usuário administrador

```powershell
python manage.py createsuperuser
```

Informe o nome de usuário e a senha solicitados pelo Django.

### 7. Iniciar o servidor

```powershell
python manage.py runserver
```

Acesse o sistema pelo navegador:

http://127.0.0.1:8000/

## Banco de dados

O sistema utiliza SQLite por meio do Django ORM.

O banco de dados local é armazenado no arquivo:

`db.sqlite3`

Esse arquivo é criado na raiz do projeto após a inicialização e aplicação das migrations.

## Backup e restauração

Na primeira versão, o backup do banco de dados é manual.

### Como realizar o backup

1. Encerre o servidor Django e certifique-se de que não há operações utilizando o banco.
2. Localize o arquivo `db.sqlite3` na raiz do projeto.
3. Copie o arquivo para um local seguro, preferencialmente em outro dispositivo ou local distinto do computador.
4. Identifique a cópia com a data em que o backup foi realizado.

Exemplo de nome:

`backup_central_varejo_2026-11-08.sqlite3`

Recomenda-se estabelecer uma frequência de backup adequada à rotina de utilização do sistema.

### Como restaurar o backup

1. Encerre o servidor Django.
2. Preserve uma cópia do banco atual, caso ainda exista.
3. Copie o arquivo de backup para a raiz do projeto.
4. Renomeie a cópia restaurada para `db.sqlite3`.
5. Inicie novamente o servidor e confira os dados.

**Importante:** não armazene backups apenas no mesmo computador utilizado pelo sistema. O backup deve permanecer em local distinto e seguro.

O sistema não implementa backup automático nesta primeira versão.

## Testes

Para executar todos os testes automatizados:

```powershell
python manage.py test -v 2
```

Para verificar a configuração do Django:

```powershell
python manage.py check
```

## Estrutura do projeto

```text
centraldovarejo/
├── central_varejo/    # Configurações e rotas principais
├── usuarios/          # Autenticação e gerenciamento de usuários
├── produtos/          # Cadastro e gerenciamento de produtos
├── estoque/           # Controle e movimentação de estoque
├── vendas/             # Carrinho, vendas e histórico
├── relatorios/         # Relatórios gerenciais
├── templates/          # Templates HTML
├── static/             # Arquivos CSS, JavaScript e imagens
├── manage.py           # Gerenciador do Django
├── requirements.txt    # Dependências do projeto
└── README.md           # Documentação e instruções
```

## Controle de versão

O projeto utiliza Git para controle de versão.

As alterações são registradas por meio de commits descritivos.

## Observações

Este projeto foi desenvolvido com finalidade acadêmica. A configuração atual está direcionada à execução local e não representa uma configuração pronta para produção.