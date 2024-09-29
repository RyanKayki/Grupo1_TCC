# TCC: CRUD para Manutenção de Escola

## Descrição

Este projeto é um Trabalho de Conclusão de Curso (TCC) desenvolvido para o SESI, com foco em manutenção escolar. O aplicativo permite que funcionários e diretores cadastrem locais e equipamentos da escola, além de fazerem chamados para a manutenção. O administrador do sistema possui a capacidade de cadastrar funcionários, locais e equipamentos, facilitando a gestão e a organização das operações de manutenção.

## Tecnologias Utilizadas

- **Git**: Sistema de controle de versão para gerenciar o código do projeto.
- **GitHub**: Plataforma online para hospedar o repositório do projeto e facilitar a colaboração.
- **Flask**: Framework web em Python para o desenvolvimento do lado do servidor.
- **HTML e CSS (Bootstrap)**: Linguagens de marcação e estilização para criar o front-end do aplicativo.
- **SQL**: Utilizado para a criação e manipulação do banco de dados, armazenando informações sobre os locais, equipamentos e usuários.

## Funcionalidades Principais

O aplicativo terá as seguintes funcionalidades:

- **Cadastro de Locais**: Diretores podem cadastrar novos locais da escola, especificando detalhes como nome e número.
- **Cadastro de Equipamentos**: Funcionários e diretores podem cadastrar equipamentos, incluindo informações como nome, descrição e quantidade.
- **Chamados de Manutenção**: Funcionários podem registrar solicitações de manutenção para os locais e equipamentos cadastrados.
- **Administração de Funcionários**: O administrador pode cadastrar novos funcionários e gerenciar seus dados.
- **Visualização de Cadastros**: Todos os usuários podem visualizar os cadastros de locais, equipamentos e funcionários.
- **Visualização de Cadastros**: Edição e Exclusão de Registros: O administrador pode editar ou excluir registros de funcionários, locais e equipamentos, garantindo que as informações estejam sempre atualizadas.
## Estrutura do Projeto

- **adm/**: Diretório que contém as funcionalidades relacionadas ao administrador do sistema.
  - **adm.py**: Código relacionado às operações de administração.
  - **templates/**: Diretório contendo os modelos HTML para as páginas administrativas.
    - **adm.html**: Modelo para a página de administração.
    - **cadastro.html**: Modelo para a página de cadastro.
    - **cadidados.html**: Modelo para exibir os cadastrados.
    - **modelAdm.html**: Modelo base para as páginas administrativas.

- **connection/**: Diretório que contém a lógica de conexão com o banco de dados.
  - **connection.py**: Código responsável pela conexão com o banco de dados.

- **func/**: Diretório que contém as funcionalidades para os funcionários.
  - **func.py**: Código relacionado às operações dos funcionários.
  - **templates/**: Diretório contendo os modelos HTML para as páginas dos funcionários.
    - **FuncHome.html**: Modelo para a página inicial dos funcionários.

- **session/**: Diretório responsável pela gestão de sessões de usuário.
  - **session.py**: Código responsável pela manipulação de sessões.
  - **templates/**: Diretório contendo os modelos HTML para as páginas de login.
    - **login.html**: Modelo para a página de login.
    - **modelSession.html**: Modelo base para as páginas de sessão.

- **static/**: Diretório que contém arquivos estáticos utilizados pelo aplicativo.
  - **IMG/**: Pasta para imagens.
  - **JS/**: Pasta para arquivos JavaScript.

- **tec/**: Diretório relacionado a funcionalidades técnicas do aplicativo.
  - **tec.py**: Código relacionado às operações técnicas.
  - **templates/**: Diretório contendo os modelos HTML para as páginas técnicas.
    - **TecHome.html**: Modelo para a página inicial técnica.

## Licença


Este projeto é fornecido sob a Licença [MIT](LICENSE).

## Contato

- [Ádillan, Cecilia, Laura Rodrigues, Maria Clara e Ryan Kayki]: Autores do Projeto.


- [Rafael Ribas]: Instrutor de Programação Web Front-End👊.


- [João Paulo]: Instrutor de Programação Web Back-End👊.


---


© [2024] Sesi Senai Itapeva