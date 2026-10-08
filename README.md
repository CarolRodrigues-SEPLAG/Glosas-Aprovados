# Transformador de relatório SIHD2

Aplicativo Streamlit com login compartilhado. Recebe um relatório mensal
`.QRP` do SIHD2, extrai os dados por CNES e gera uma planilha Excel.

## Campos exportados

- Código CNES
- Nome da unidade de saúde
- Competência
- Valor apresentado
- Valor aprovado
- Valor do serviço hospitalar
- Valor do serviço profissional

No relatório de origem, “Apres” e “Aprov” são quantidades; são exportadas como
os valores apresentado e aprovado. Os serviços hospitalar e profissional são
os totais monetários consolidados exibidos por CNES, incluindo próprio e
terceiro.

## Executar localmente

Requer Python 3.10 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python .\gerar_segredo_login.py
```

O gerador pede um usuário e uma senha duas vezes. A senha não aparece na tela e
não é gravada em arquivo; o programa imprime um bloco com o usuário, um salt
aleatório e o hash PBKDF2-SHA256. Copie as três linhas impressas.

Crie `.streamlit\secrets.toml` na pasta do projeto com este formato, substituindo
os valores pelas linhas geradas:

```toml
[auth]
username = "usuario_da_equipe"
password_salt = "salt_gerado"
password_hash = "hash_gerado"
```

Inicie o app:

```powershell
streamlit run app.py
```

Abra o endereço local apresentado pelo Streamlit, entre com o usuário e senha
definidos, envie o `.QRP` do mês e selecione **Baixar tabela em Excel**. Use
**Sair** para encerrar a sessão autenticada.

O arquivo `.streamlit\secrets.toml` contém configuração privada e não deve ser
enviado ao GitHub ou compartilhado. A senha não é guardada pela aplicação: o
verificador usa PBKDF2-SHA256 com 600 mil iterações e salt aleatório.

## Publicar no Streamlit Community Cloud

1. Coloque o código deste projeto em um repositório GitHub. Se o código não
   precisar ser público, escolha um repositório privado.
2. Acesse Streamlit Community Cloud e conecte a conta GitHub que tem acesso ao
   repositório.
3. Crie um app, escolha o repositório e branch, e defina `app.py` como arquivo
   principal.
4. Abra **Advanced settings / Secrets** nas configurações do app e cole as três
   linhas geradas em uma seção `[auth]`, no formato do exemplo acima. Não
   publique a senha, o hash ou o salt em arquivos do repositório.
5. Implante o app. O Cloud instala as bibliotecas listadas em
   `requirements.txt`; após a inicialização, o endereço do app estará disponível
   no painel.

O upload é processado pela instância remota do app. Antes de usar dados
institucionais ou publicar, confirme que a hospedagem externa é autorizada pela
organização. O aplicativo não salva o arquivo em disco nem mantém histórico
intencionalmente, mas isso não substitui a aprovação institucional das regras
de tratamento de dados.

## Como cada script funciona

### `app.py` — interface, acesso e exportação

1. Importa o Streamlit, o Pandas e o OpenPyXL, usados respectivamente para
   interface web, tabela de visualização e arquivo `.xlsx`.
2. Define a ordem e os nomes das sete colunas exportadas.
3. `_to_dataframe` transforma os registros do parser em uma tabela para
   pré-visualização no navegador.
4. `_make_excel` cria a planilha “Aprovados por CNES”, escreve cabeçalho e
   unidades, aplica estilo ao cabeçalho, congela a primeira linha, habilita
   filtros e formata os valores monetários.
5. `_show_login` lê usuário, salt e hash de `st.secrets`; se a configuração
   estiver ausente, interrompe o app com uma mensagem clara. O formulário
   valida a senha pelo módulo `auth.py`; em caso de sucesso, marca a sessão
   como autenticada.
6. Antes de exibir o transformador, verifica a autenticação. A barra lateral
   oferece **Sair**, que encerra o estado autenticado da sessão.
7. `st.file_uploader` aceita arquivos `.QRP`. O parser extrai os dados; erros de
   formato são mostrados na tela em vez de exportar uma tabela incompleta.
8. Exibe competência e quantidade de unidades, mostra a tabela e prepara o
   botão de download com nome de arquivo baseado na competência.

### `auth.py` — verificação de credenciais

1. Decodifica o salt e o hash hexadecimal guardados em segredos.
2. Recusa configurações malformadas, salt curto ou hash com tamanho inesperado.
3. Calcula PBKDF2-SHA256 da senha informada com 600 mil iterações.
4. Compara usuário e hash com comparação de tempo constante. O valor da senha
   original não é armazenado.

### `gerar_segredo_login.py` — preparação do login

1. Solicita um nome de usuário e a senha duas vezes sem exibir os caracteres.
2. Gera um salt aleatório de 16 bytes.
3. Calcula o hash PBKDF2-SHA256 usando os mesmos parâmetros de `auth.py`.
4. Imprime as linhas TOML para configuração manual; não cria nem altera arquivos.

### `qrp_parser.py` — leitura do formato QRP

1. Localiza no binário os registros de texto UTF-16LE usados pelo relatório
   SIHD2 e extrai a competência.
2. Reconhece os registros com CNES de sete dígitos e nome da unidade.
3. Associa, para cada unidade, os valores de hospitalar, profissional, total,
   aprovado e apresentado; interpreta números no formato brasileiro.
4. Mantém CNES como texto, preservando zeros à esquerda, e guarda valores
   monetários como `Decimal`.
5. Lança `QrpFormatError` quando o arquivo está vazio, não tem competência ou
   não contém dados que possam ser associados com segurança.

### `tests/test_qrp_parser.py` e `tests/test_auth.py` — testes

Os testes constroem registros QRP sintéticos para verificar competência,
quantidades, totais, artefatos de renderização e rejeição de arquivos
ilegíveis. Os testes de autenticação verificam senha correta/incorreta e
configuração inválida.

## Testes

```powershell
python -m unittest discover -s tests -v
```
