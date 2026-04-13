# Sicer Architet Agent

Agent locale standalone per GitHub Copilot CLI costruito con **LangGraph** e **MCP**.

E' pensato per **codebase multi-modulo** e aiuta Copilot a rispondere a domande come:

- quale modulo devo modificare per primo?
- quali altri moduli sono impattati?
- quali file devo leggere prima di fare una patch?
- qual e' un ordine sicuro per una modifica cross-modulo?

## Cosa offre

Questo progetto espone un server MCP con tre tool iniziali:

- `detect_project_type`
- `list_modules`
- `plan_multimodule_change`

Il flusso di pianificazione e' orchestrato con LangGraph, ma nella prima versione resta deterministico cosi' da poter girare localmente senza dipendere da chiamate a modelli esterni.

## Installazione

### Installazione con una riga

```bash
curl -fsSL https://raw.githubusercontent.com/elisimon-g/sicer-architet-agent/main/install.sh | bash
```

L'installer:

- installa la CLI `sicer-architet-agent`
- installa la skill opzionale di Copilot in `~/.copilot/skills/sicer`
- registra automaticamente il server MCP in `~/.copilot/mcp-config.json`
- lascia Copilot CLI pronto all'uso dopo un riavvio oppure dopo `/skills reload`

### Opzione 1: installazione locale editable

```bash
cd sicer-architet-agent
python -m pip install -e .
```

### Opzione 2: esecuzione con uv

```bash
cd sicer-architet-agent
uv sync
```

## Avvio locale

```bash
sicer-architet-agent
```

Il server usa il trasporto **STDIO** per gli host MCP.

## Integrazione con GitHub Copilot CLI

L'installer configura automaticamente Copilot CLI con un server MCP chiamato `sicer` che avvia:

```text
sicer-architet-agent
```

Se preferisci `uv`, puoi puntare Copilot CLI a:

```text
uv --directory /absolute/path/to/sicer-architet-agent run sicer-architet-agent
```

Esempio di configurazione:

```json
{
  "mcpServers": {
    "architect-agent": {
      "command": "sicer-architet-agent",
      "args": []
    }
  }
}
```

## Skill opzionale

Il repository include anche una skill opzionale nella cartella `skills/sicer`.

Puoi aggiungerla in Copilot CLI con `/skills add /absolute/path/to/sicer-architet-agent/skills`
e ricaricarla con `/skills reload`.

Esempio di prompt:

```text
Use /sicer to plan a safe change in this Maven monolith.
```

## Sviluppo

Esegui i test:

```bash
python -m unittest discover -s tests -v
```

## Comportamento dei tool

### `detect_project_type`

Analizza un workspace e riassume i segnali architetturali e di build prevalenti.

### `list_modules`

Legge il `pom.xml` root e quelli dei moduli figli, riportando moduli, packaging, dipendenze e indicatori rapidi.

### `plan_multimodule_change`

Costruisce un piano strutturato con:

- modulo primario
- moduli secondari
- entry point probabili
- file candidati da ispezionare
- rischi della modifica
- ordine consigliato di implementazione
