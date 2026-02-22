# Ferramenta de Anotação de Textos (Português Brasileiro)

Esta ferramenta permite que anotadores de pesquisa leiam respostas curtas sobre tópicos políticos e as classifiquem quanto a emoção, sentimento, fundamentos morais e posicionamento político. Ela roda no navegador, salva o progresso automaticamente e cria um arquivo de saída individual para cada anotador.

## O Que os Anotadores Fazem

Cada anotador lê a resposta de um participante a uma afirmação política — junto com o contexto de qual afirmação ele respondeu e se concordou ou discordou — e responde a quatro conjuntos de perguntas:

- **Emoções** — Avalie a intensidade de cada emoção (ansiedade, raiva, tristeza, alegria, otimismo, frustração, medo e esperança) em uma escala de 1 a 7.
- **Sentimento** — Classifique o texto como Positivo, Neutro ou Negativo, e avalie em uma escala de 1 a 7.
- **Fundamentos Morais** — Escolha o fundamento moral que melhor representa o texto entre: Cuidado, Justiça, Lealdade, Autoridade, Pureza, Liberdade, Honestidade e Autodisciplina. Depois, indique a orientação (individualizante ou vinculante).
- **Inferência Política** — Estime o posicionamento político do autor: Esquerda, Direita, Centro/Outro ou Não é possível determinar.

## Estrutura do Projeto

```
.
├── server.py              # Servidor Python que carrega os dados e salva as anotações
├── annotation_tool.html   # Interface de anotação (aplicação de página única)
├── INSTRUCTIONS.html      # Guia passo a passo para anotadores
├── annotations_empty.csv  # CSV modelo com os textos a serem anotados
├── statements.txt         # Mapeamento de códigos de afirmações para o texto em português
└── .gitignore
```

## Requisitos

- **Python 3.6+** — usa apenas a biblioteca padrão, então não é necessário instalar nenhum pacote.
- Um navegador moderno (Chrome, Firefox, Safari ou Edge).

## Como Começar

### 1. Prepare seus dados

Coloque um arquivo CSV chamado `annotations_empty.csv` na raiz do projeto. Ele precisa ter estas colunas:

| Coluna | O que contém |
|---|---|
| `rowid` | ID único da linha (usado como chave de anotação e para unir ao dataframe principal) |
| `ResponseId` | ID único do participante |
| `statement` | Código da afirmação política (ex.: `climate_change`, `gun_laws`) |
| `agree` | Se o participante concordou ou discordou (Concordo/Discordo/Não tenho certeza) |
| `X_describe` | A resposta em texto livre do participante — é isto que os anotadores leem e classificam |

### 2. Leia as instruções

Antes de tudo, abra `INSTRUCTIONS.html` no seu navegador. Ele explica a tarefa completa de anotação — o que você vai ler, o que vai classificar e como usar a ferramenta. Também ensina como instalar o Python e iniciar o servidor no Mac e no Windows.

### 3. Inicie o servidor

```bash
python3 server.py        # Mac / Linux
python server.py         # Windows
```

Você verá um banner confirmando que o servidor está rodando em **http://localhost:8000**.

### 4. Abra a ferramenta e comece a anotar

Acesse [http://localhost:8000](http://localhost:8000) no seu navegador. Digite um nome de usuário e clique em **Começar a Anotar**. A ferramenta cria um arquivo de saída pessoal para aquele usuário (`annotations_[usuario].csv`) e você pode começar.

## Como Funciona

### O servidor (`server.py`)

Um pequeno servidor HTTP em Python — sem frameworks, sem dependências — que faz três coisas:

1. **Serve os arquivos do frontend** (HTML, CSS, JS) do diretório do projeto.
2. **Carrega os dados do modelo** do `annotations_empty.csv` e os envia ao navegador.
3. **Lê e grava o CSV de cada anotador** para que o progresso persista entre sessões.

Estes são os endpoints da API que ele expõe:

| Método | Endpoint | O que faz |
|---|---|---|
| `GET` | `/api/template` | Envia todas as linhas do CSV modelo |
| `GET` | `/api/annotations?username=X` | Busca as anotações salvas de um usuário |
| `GET` | `/api/check-user?username=X` | Verifica se um arquivo de usuário já existe |
| `GET` | `/api/list-users` | Lista todos os arquivos de anotadores existentes com contagem de progresso |
| `POST` | `/api/init-user` | Cria um novo `annotations_[usuario].csv` a partir do modelo |
| `POST` | `/api/save` | Grava as anotações atuais no CSV do usuário |

### O frontend (`annotation_tool.html`)

Tudo está em um único arquivo HTML — estilos, marcação e lógica em um só lugar. Aqui está o que ele oferece:

- **Tela de configuração** — Digite um nome de usuário; a ferramenta detecta se você tem uma sessão anterior.
- **Interface de anotação** — O texto permanece fixo no topo enquanto você navega pelas perguntas. Uma barra de progresso acompanha o seu avanço.
- **Validação** — Você deve responder todas as perguntas antes de avançar.
- **Duplo salvamento** — A ferramenta grava no CSV do servidor *e* armazena um backup no `localStorage` do navegador, para que você não perca trabalho mesmo se o servidor tiver problemas.
- **Retomada de sessão** — Volte mais tarde, digite o mesmo nome de usuário e continue de onde parou.
- **Navegação** — Avance, volte ou pule para qualquer item pelo número.
- **Tela de conclusão** — Quando terminar, baixe suas anotações como CSV ou revise-as.

### Formato de saída

A ferramenta salva o trabalho de cada anotador em `annotations_[usuario].csv`. Este arquivo contém as colunas originais dos dados mais todas as colunas de anotação:

```
annotator_id, emotion_anxiety_likert, emotion_anger_likert, emotion_sadness_likert,
emotion_joy_likert, emotion_optimism_likert, emotion_frustration_likert,
emotion_fear_likert, emotion_hope_likert, sentiment_categorical,
sentiment_likert, mf_best, mf_orientation, political_guess
```

## Para Anotadores

Se você é um anotador, abra `INSTRUCTIONS.html` no seu navegador. Ele explica tudo:

- Como instalar o Python (Mac e Windows)
- Como iniciar e parar o servidor
- Como usar a interface de anotação
- Como fazer pausas e continuar depois
- O que fazer quando algo dá errado

## Solução de Problemas

**"Address already in use"** — Uma instância anterior do servidor ainda está rodando. No Mac, encerre com `lsof -ti:8000 | xargs kill -9`. No Windows, feche todas as janelas do terminal e tente novamente.

**"python not found"** — Você precisa instalar o Python 3 em [python.org](https://www.python.org/downloads/). No Windows, certifique-se de marcar "Add Python to PATH" durante a instalação.

**A página não carrega** — Verifique se o servidor está rodando no seu terminal e se você está usando `http://` (não `https://`).

**Progresso não restaurado** — Certifique-se de digitar exatamente o mesmo nome de usuário que usou antes e clique em **Retomar Sessão**.
