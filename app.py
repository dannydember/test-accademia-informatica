"""
APP.PY - Fase 6.2: Estetica e Icone (Spostamento pulsante Avorio)
"""
import streamlit as st
import importlib
import os
import random
import json
import hashlib
import re
import base64
import streamlit.components.v1 as components

st.set_page_config(page_title="Test ITS", page_icon="🎓", layout="centered")

# =====================================================================
# CARICAMENTO ICONE
# =====================================================================
CARTELLA_ICONE = "icone"

@st.cache_data
def carica_icona_base64(nome_file):
    percorso = os.path.join(CARTELLA_ICONE, nome_file)
    if not os.path.exists(percorso):
        return None
    try:
        with open(percorso, "rb") as f:
            dati = f.read()
            return base64.b64encode(dati).decode("utf-8")
    except Exception:
        return None

def mostra_icona(nome_file, larghezza=80):
    b64 = carica_icona_base64(nome_file)
    if b64:
        st.markdown(
            f'<div style="text-align: center;"><img src="data:image/png;base64,{b64}" width="{larghezza}"></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown("<div style='text-align: center; font-size: 40px;'>🖼️</div>", unsafe_allow_html=True)

# =====================================================================
# GESTIONE FILE DI RIPASSO (JSON)
# =====================================================================
CARTELLA_DATI = "dati"
FILE_SBAGLIATE = os.path.join(CARTELLA_DATI, "domande_sbagliate.json")

def _chiave_domanda(domanda):
    base = domanda.get("domanda", "") + "|" + "|".join(domanda.get("opzioni", []))
    return hashlib.sha1(base.encode("utf-8")).hexdigest()

def carica_sbagliate():
    if not os.path.exists(FILE_SBAGLIATE):
        return []
    try:
        with open(FILE_SBAGLIATE, "r", encoding="utf-8") as f:
            dati = json.load(f)
            return dati if isinstance(dati, list) else []
    except Exception:
        return []

def salva_sbagliate(lista):
    os.makedirs(CARTELLA_DATI, exist_ok=True)
    with open(FILE_SBAGLIATE, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

def aggiungi_sbagliata(domanda):
    sbagliate = carica_sbagliate()
    if _chiave_domanda(domanda) in {_chiave_domanda(d) for d in sbagliate}:
        return
    sbagliate.append(domanda)
    salva_sbagliate(sbagliate)

def rimuovi_sbagliata(domanda):
    sbagliate = carica_sbagliate()
    k = _chiave_domanda(domanda)
    nuove = [d for d in sbagliate if _chiave_domanda(d) != k]
    if len(nuove) != len(sbagliate):
        salva_sbagliate(nuove)

def svuota_sbagliate():
    salva_sbagliate([])

# =====================================================================
# PARSER FILE TXT
# =====================================================================
_RE_OPZIONE = re.compile(r"^\s*([A-Za-z]|\d+)\s*[\)\.\-:]\s*(.+?)\s*$")

def _parse_test_txt(contenuto_testo):
    righe = contenuto_testo.splitlines()
    domande = []
    opzioni = []
    risposta = None
    spiegazione = ""
    testo_domanda = None
    in_attesa_testo_domanda = False

    def _pulisci_riga(r):
        r = r.strip()
        if len(r) >= 2 and r[0] == r[-1] and r[0] in ("'", '"'):
            r = r[1:-1].strip()
        return r

    def _chiudi_blocco():
        nonlocal domande, opzioni, risposta, spiegazione, testo_domanda
        if testo_domanda is None:
            return
        if len(opzioni) != 4:
            return

        idx = 0
        if risposta:
            match_r = re.search(r"[A-D1-4]", risposta.upper())
            if match_r:
                r_val = match_r.group(0)
                if r_val in ("A", "B", "C", "D"):
                    idx = "ABCD".index(r_val)
                else:
                    idx = int(r_val) - 1

        domande.append({
            "domanda": testo_domanda,
            "opzioni": list(opzioni),
            "risposta": "ABCD"[idx],
            "spiegazione": spiegazione.strip(),
        })
        
        opzioni.clear()
        risposta = None
        spiegazione = ""
        testo_domanda = None

    for riga_grezza in righe:
        riga = _pulisci_riga(riga_grezza)
        if not riga or riga.startswith("#"):
            continue

        if in_attesa_testo_domanda:
            _chiudi_blocco()
            testo_domanda = riga
            in_attesa_testo_domanda = False
            continue

        riga_upper = riga.upper()

        if riga_upper == "DOMANDA" or riga_upper.startswith("DOMANDA:"):
            _chiudi_blocco()
            if ":" in riga:
                parti = riga.split(":", 1)
                if parti[1].strip():
                    testo_domanda = parti[1].strip()
                else:
                    in_attesa_testo_domanda = True
            else:
                in_attesa_testo_domanda = True
            continue

        if riga_upper.startswith("RISPOSTA"):
            parti = riga.split(":", 1)
            if len(parti) > 1:
                risposta = parti[1].strip()
            else:
                match_r = re.search(r"([A-D1-4])", riga_upper)
                if match_r:
                    risposta = match_r.group(1)
            continue

        if riga_upper.startswith("SPIEGAZIONE"):
            parti = riga.split(":", 1)
            if len(parti) > 1:
                spiegazione = parti[1].strip()
            continue

        m_opzione = _RE_OPZIONE.match(riga)
        if m_opzione:
            opzioni.append(m_opzione.group(2))
            continue

        if testo_domanda is not None and risposta is not None:
            if spiegazione:
                spiegazione += " " + riga
            else:
                spiegazione = riga

    _chiudi_blocco()
    return domande

# =====================================================================
# CONFIGURAZIONE DEI TEST DISPONIBILI
# =====================================================================
TEST_DISPONIBILI = [
    {"nome": "Informatica", "modulo": "dati.informatica_300", "icona": "tastiera.png", "colore": "#2E8B57"},
    {"nome": "Inglese", "modulo": "dati.inglese_A2", "icona": "inglese.png", "colore": "#4682B4"},
    {"nome": "Logica", "modulo": "dati.logica_150", "icona": "logica.png", "colore": "#8E44AD"},
    {"nome": "Cultura Generale", "modulo": "dati.cultura_200", "icona": "cultura.png", "colore": "#D2691E"},
]

# =====================================================================
# FUNZIONI DI SUPPORTO
# =====================================================================

@st.cache_data
def carica_database(nome_modulo):
    try:
        modulo = importlib.import_module(nome_modulo)
        return {
            "nome_test": getattr(modulo, "NOME_TEST", "Test senza nome"),
            "colore_tema": getattr(modulo, "COLORE_TEMA", "#4682B4"),
            "soglia": getattr(modulo, "SOGLIA_SUPERAMENTO", 60),
            "database": modulo.TUTTI_I_TEST
        }
    except Exception:
        return None

def inizializza_stato():
    if "fase" not in st.session_state:
        st.session_state.fase = "menu"
    if "modulo_attivo" not in st.session_state:
        st.session_state.modulo_attivo = None
    if "domande_test" not in st.session_state:
        st.session_state.domande_test = []
    if "indice" not in st.session_state:
        st.session_state.indice = 0
    if "corrette" not in st.session_state:
        st.session_state.corrette = 0
    if "sbagliate" not in st.session_state:
        st.session_state.sbagliate = []
    if "risposta_data" not in st.session_state:
        st.session_state.risposta_data = None

inizializza_stato()

# =====================================================================
# LOGICA DEL TEST
# =====================================================================

def avvia_test(nome_modulo, da_ripasso=False, domande_importate=None, nome_test_importato="Test Importato"):
    if domande_importate is not None:
        tutte_le_domande = domande_importate
        nome_test_attivo = nome_test_importato
        colore_attivo = "#16A085"
        soglia_attiva = 60
    elif da_ripasso:
        tutte_le_domande = carica_sbagliate()
        nome_test_attivo = "Ripasso"
        colore_attivo = "#C0392B"
        soglia_attiva = 60
    else:
        dati_modulo = carica_database(nome_modulo)
        if not dati_modulo:
            st.error(f"Impossibile caricare il modulo {nome_modulo}")
            return
            
        tutte_le_domande = []
        for num_test, contenuto in dati_modulo["database"].items():
            for i in range(len(contenuto["domande"])):
                tutte_le_domande.append({
                    "domanda": contenuto["domande"][i],
                    "opzioni": [contenuto["A"][i], contenuto["B"][i], contenuto["C"][i], contenuto["D"][i]],
                    "risposta": contenuto["risposte"][i],
                    "spiegazione": contenuto["spiegazioni"][i] if "spiegazioni" in contenuto else ""
                })
        nome_test_attivo = dati_modulo["nome_test"]
        colore_attivo = dati_modulo["colore_tema"]
        soglia_attiva = dati_modulo["soglia"]

    if not tutte_le_domande:
        st.warning("Nessuna domanda disponibile.")
        return

    for d in tutte_le_domande:
        if "risposta" not in d and "indice_corretto" in d:
            idx = d["indice_corretto"]
            d["risposta"] = "ABCD"[idx] if 0 <= idx <= 3 else "A"

    num_domande_desiderate = 30 
    if len(tutte_le_domande) > num_domande_desiderate:
        domande_scelte = random.sample(tutte_le_domande, num_domande_desiderate)
    else:
        domande_scelte = tutte_le_domande

    st.session_state.modulo_attivo = "importato" if domande_importate else ("ripasso" if da_ripasso else nome_modulo)
    st.session_state.nome_test_attivo = nome_test_attivo
    st.session_state.colore_attivo = colore_attivo
    st.session_state.soglia_attiva = soglia_attiva
    st.session_state.domande_test = domande_scelte
    st.session_state.indice = 0
    st.session_state.corrette = 0
    st.session_state.sbagliate = []
    st.session_state.risposta_data = None
    st.session_state.fase = "test"

def torna_al_menu():
    st.session_state.fase = "menu"
    st.session_state.modulo_attivo = None
    st.session_state.domande_test = []
    st.session_state.indice = 0
    st.session_state.corrette = 0
    st.session_state.sbagliate = []
    st.session_state.risposta_data = None

def registra_risposta(lettera):
    domanda = st.session_state.domande_test[st.session_state.indice]
    st.session_state.risposta_data = lettera
    risposta_corretta = domanda["risposta"]

    if lettera == risposta_corretta:
        st.session_state.corrette += 1
        if st.session_state.modulo_attivo in ["ripasso", "importato"]:
            rimuovi_sbagliata(domanda)
    else:
        st.session_state.sbagliate.append(domanda)
        aggiungi_sbagliata(domanda)

def prossima_domanda():
    st.session_state.indice += 1
    st.session_state.risposta_data = None
    if st.session_state.indice >= len(st.session_state.domande_test):
        st.session_state.fase = "risultato"

# =====================================================================
# COMPONENTE JAVASCRIPT PER LA TASTIERA
# =====================================================================
def abilita_tastiera():
    js_code = """
    <script>
    const handleKeyDown = (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        const key = e.key.toUpperCase();
        
        if (['A', 'B', 'C', 'D'].includes(key)) {
            const buttons = parent.document.querySelectorAll('button');
            for (let btn of buttons) {
                const text = btn.innerText.trim();
                const cleanText = text.replace(/\\*/g, '');
                if (cleanText.startsWith(key + ')')) {
                    btn.click();
                    e.preventDefault();
                    e.stopPropagation();
                    break;
                }
            }
        }
        
        if (e.key === 'Enter') {
            const buttons = parent.document.querySelectorAll('button');
            for (let btn of buttons) {
                const text = btn.innerText.trim();
                if (text.includes('Prossima')) {
                    btn.click();
                    e.preventDefault();
                    e.stopPropagation();
                    break;
                }
            }
        }
    };
    
    if (!parent.document.hasKeyboardListener) {
        parent.document.addEventListener('keydown', handleKeyDown, true);
        parent.document.hasKeyboardListener = true;
    }
    </script>
    """
    components.html(js_code, height=0, width=0)

# =====================================================================
# SCHERMATE
# =====================================================================

def schermata_menu():
    st.markdown("<h1 style='text-align: center; color: #4682B4;'>🎓 SCEGLI IL TEST</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Seleziona una materia per iniziare a esercitarti.</p>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2 = st.columns(2)
    colonne = [col1, col2, col1, col2]
    
    for i, test in enumerate(TEST_DISPONIBILI):
        with colonne[i]:
            mostra_icona(test["icona"], larghezza=90)
            st.markdown(f"<h3 style='text-align: center; color: {test['colore']};'>{test['nome']}</h3>", unsafe_allow_html=True)
            st.caption("Database pronto")
            if st.button(f"Inizia {test['nome']}", key=f"btn_{test['nome']}", use_container_width=True):
                avvia_test(test['modulo'])
                st.rerun()
            st.write("")

    st.divider()
    n_sbagliate = len(carica_sbagliate())
    st.markdown("<h3 style='text-align: center;'>🔁 RIPASSO</h3>", unsafe_allow_html=True)
    mostra_icona("ripasso.png", larghezza=70)
    
    if n_sbagliate > 0:
        st.markdown(f"<p style='text-align: center;'>Hai <b>{n_sbagliate}</b> domande sbagliate da ripassare.</p>", unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            if st.button("Inizia Ripasso", type="primary", use_container_width=True):
                avvia_test("ripasso", da_ripasso=True)
                st.rerun()
            if st.button("🗑️ Svuota Ripasso", use_container_width=True):
                svuota_sbagliate()
                st.rerun()
    else:
        st.info("Il ripasso è vuoto. Fai qualche test: le domande sbagliate finiranno qui.")

    st.divider()
    st.markdown("<h3 style='text-align: center;'>📥 IMPORTA TEST</h3>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("Carica un file .txt", use_container_width=True):
            st.session_state.fase = "import"
            st.rerun()

def schermata_import():
    st.title("📥 Importa Test da TXT")
    st.write("Carica un file di testo formattato correttamente per creare un test al volo.")
    
    uploaded_file = st.file_uploader("Scegli un file .txt", type="txt")
    
    if uploaded_file is not None:
        contenuto = uploaded_file.getvalue().decode("utf-8")
        domande = _parse_test_txt(contenuto)
        
        if not domande:
            st.error("Nessuna domanda valida trovata nel file. Controlla il formato.")
        else:
            st.success(f"Trovate {len(domande)} domande valide!")
            if st.button("Inizia il test importato", type="primary", use_container_width=True):
                nome_file = uploaded_file.name.replace(".txt", "").replace("_", " ").title()
                avvia_test(None, domande_importate=domande, nome_test_importato=nome_file)
                st.rerun()
                
    st.divider()
    if st.button("🏠 Torna al menu"):
        torna_al_menu()
        st.rerun()

def schermata_test():
    domande = st.session_state.domande_test
    idx = st.session_state.indice
    domanda = domande[idx]
    
    nome_test = st.session_state.get("nome_test_attivo", "Test")
    colore = st.session_state.get("colore_attivo", "#4682B4")
    
    st.progress((idx) / len(domande), text=f"Domanda {idx + 1} di {len(domande)}")
    st.markdown(f"<h3 style='color: {colore};'>{nome_test}</h3>", unsafe_allow_html=True)

    st.markdown(f"**{domanda['domanda']}**")

    abilita_tastiera()

    if st.session_state.risposta_data is None:
        for lettera, testo in zip("ABCD", domanda["opzioni"]):
            if st.button(f"**{lettera})** {testo}", key=f"opt_{lettera}", use_container_width=True):
                registra_risposta(lettera)
                st.rerun()
    else:
        lettera_data = st.session_state.risposta_data
        lettera_corretta = domanda["risposta"]

        for lettera, testo in zip("ABCD", domanda["opzioni"]):
            if lettera == lettera_corretta:
                st.success(f"✅ **{lettera})** {testo}  ← risposta corretta")
            elif lettera == lettera_data and lettera != lettera_corretta:
                st.error(f"❌ **{lettera})** {testo}  ← la tua risposta")
            else:
                st.write(f"**{lettera})** {testo}")

        if domanda.get("spiegazione"):
            st.info(f"💡 {domanda['spiegazione']}")

        if st.button("➡️ Prossima domanda", type="primary", use_container_width=True):
            prossima_domanda()
            st.rerun()

    st.divider()
    if st.button("🏠 Torna al menu"):
        torna_al_menu()
        st.rerun()

def schermata_risultato():
    totale = len(st.session_state.domande_test)
    corrette = st.session_state.corrette
    percentuale = (corrette / totale * 100) if totale else 0
    soglia = st.session_state.get("soglia_attiva", 60)
    superato = percentuale >= soglia

    st.title("📊 Risultato del test")
    st.write(f"**{st.session_state.get('nome_test_attivo', 'Test')}**")

    col1, col2, col3 = st.columns(3)
    col1.metric("Risposte corrette", f"{corrette}/{totale}")
    col2.metric("Percentuale", f"{percentuale:.0f}%")
    col3.metric("Soglia", f"{soglia}%")

    if superato:
        st.success(f"🎉 Test superato! Hai raggiunto il {percentuale:.0f}%.")
    else:
        st.warning(f"⚠️ Test non superato ({percentuale:.0f}%). Riprova!")

    if st.session_state.sbagliate:
        st.divider()
        st.subheader("❌ Domande sbagliate in questo test")
        for d in st.session_state.sbagliate:
            with st.expander(d["domanda"]):
                st.write(f"**Risposta corretta:** {d['risposta']}) {d['opzioni'][ord(d['risposta']) - ord('A')]}")
                if d.get("spiegazione"):
                    st.write(f"**Spiegazione:** {d['spiegazione']}")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔁 Rifai questo test", use_container_width=True):
            if st.session_state.modulo_attivo == "ripasso":
                avvia_test("ripasso", da_ripasso=True)
            elif st.session_state.modulo_attivo == "importato":
                torna_al_menu()
            else:
                avvia_test(st.session_state.modulo_attivo)
            st.rerun()
    with col_b:
        if st.button("🏠 Torna al menu", use_container_width=True):
            torna_al_menu()
            st.rerun()

# =====================================================================
# ROUTING
# =====================================================================

if st.session_state.fase == "menu":
    schermata_menu()
elif st.session_state.fase == "import":
    schermata_import()
elif st.session_state.fase == "test":
    schermata_test()
elif st.session_state.fase == "risultato":
    schermata_risultato()

# =====================================================================
# PULSANTE AVORIO
# =====================================================================
def _alterna_avorio():
    st.session_state["tema_avorio_attivo"] = not st.session_state.get(
        "tema_avorio_attivo", False
    )


def _mostra_pulsante_avorio():
    attivo = st.session_state.get("tema_avorio_attivo", False)
    st.markdown("""
    <style>
    .st-key-pulsante_avorio_fisso {
        position: fixed !important;
        top: 1.15rem !important;
        right: 14rem !important; /* Spostato a 14rem per non coprire Share */
        width: 4.5rem !important;
        z-index: 999999;
        margin: 0 !important;
        padding: 0 !important;
    }
    .st-key-pulsante_avorio_fisso button {
        width: 100%;
        min-height: 1.4rem;
        padding: 0.05rem 0.25rem;
        background-color: #F5F5DC !important;
        color: #333333 !important;
        border: 1px solid #9A9A80 !important;
        border-radius: 0.4rem;
        box-shadow: none;
    }
    .st-key-pulsante_avorio_fisso button p {
        color: #333333 !important;
        font-size: 0.72rem !important;
        line-height: 1.1 !important;
    }
    .st-key-pulsante_avorio_fisso button:focus-visible {
        outline: 2px solid #2E8B57;
        outline-offset: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container(key="pulsante_avorio_fisso"):
        st.button(
            "✓ Avorio" if attivo else "Avorio",
            key="pulsante_avorio",
            on_click=_alterna_avorio,
            help=(
                "Disattiva Avorio e torna al tema System / Light / Dark."
                if attivo else
                "Attiva Avorio. Per tornare al tema standard, premi di nuovo."
            ),
        )

    if attivo:
        st.markdown("""
        <style>
        .stApp, [data-testid="stAppViewContainer"],
        [data-testid="stMain"], [data-testid="stHeader"],
        [data-testid="stBottomBlockContainer"] {
            background-color: #F5F5DC !important;
            color: #333333 !important;
            color-scheme: light;
            --background-color: #F5F5DC;
            --secondary-background-color: #FFFFFF;
            --text-color: #333333;
        }
        [data-testid="stHeading"], [data-testid="stWidgetLabel"],
        [data-testid="stMarkdownContainer"], [data-testid="stMetric"],
        [data-testid="stMetricLabel"], [data-testid="stMetricValue"],
        [data-testid="stExpander"] summary {
            color: #333333 !important;
        }
        [data-testid="stCaptionContainer"] { color: #666666 !important; }
        [data-testid="stButton"] button[kind="secondary"],
        [data-testid="stFileUploader"] button {
            background-color: #FFFFFF !important;
            color: #333333 !important;
            border-color: #BDBDA8 !important;
        }
        [data-testid="stButton"] button[kind="primary"] {
            background-color: #2E8B57 !important;
            color: #FFFFFF !important;
            border-color: #2E8B57 !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stFileUploaderDropzone"],
        [data-testid="stExpander"] details {
            background-color: #FFFFFF !important;
            color: #333333 !important;
            border-color: #BDBDA8 !important;
        }
        [data-testid="stSelectbox"] input { color: #333333 !important; }
        [data-baseweb="popover"] [role="listbox"],
        [data-baseweb="popover"] [role="option"] {
            background-color: #FFFFFF !important;
            color: #333333 !important;
        }
        [data-testid="stMarkdownContainer"] p.sottotitolo-menu {
            color: #666666 !important;
        }
        [data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
            color: inherit !important;
        }
        .st-key-pulsante_avorio_fisso button {
            background-color: #F5F5DC !important;
            border: 2px solid #2E8B57 !important;
        }
        </style>
        """, unsafe_allow_html=True)


_mostra_pulsante_avorio()
