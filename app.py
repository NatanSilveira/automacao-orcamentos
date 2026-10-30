import base64
import os
import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
from jinja2 import Template
from xhtml2pdf import pisa

# Configuração da página no Streamlit
st.set_page_config(
    page_title="Gerador de Orçamentos - Vale do Campo",
    page_icon="📄",
    layout="wide"
)

BASE_DIR = Path(__file__).parent
TEMPLATE_PATH = BASE_DIR / "templates" / "modelo_orcamento.html"

def gerar_pdf_orcamento(dados):
    # 1. Tenta carregar a imagem da pasta assets/
    logo_path = BASE_DIR / "assets" / "logo_vale.png"
    logo_b64 = None
    
    if logo_path.exists():
        with open(logo_path, "rb") as img_file:
            logo_b64 = base64.b64encode(img_file.read()).decode("utf-8")
        print("✅ Logótipo carregado com sucesso!")
    else:
        print(f"⚠️ Atenção: Logótipo não encontrado em {logo_path.resolve()}")
    
    dados["logo_b64"] = logo_b64

    # 2. Renderiza o HTML com Jinja2
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    template = Template(html_content)
    rendered_html = template.render(**dados)

    pdf_path = BASE_DIR / f"Orcamento_{str(dados['numero_orcamento']).replace('/', '_')}.pdf"

    # 3. Converte para PDF
    with open(pdf_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(rendered_html, dest=pdf_file, encoding='utf-8')

    if pisa_status.err:
        raise Exception("Erro ao converter HTML para PDF.")

    return pdf_path

# Visual da Interface
st.title("📄 Gerador de Orçamentos — Vale do Campo")

with st.form("form_orcamento"):
    st.subheader("1. Informações do Orçamento e Cliente")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        numero_orc = st.text_input("Número do Orçamento", value=f"{datetime.date.today().year}/{datetime.datetime.now().strftime('%M%S')}")
        cliente = st.text_input("Nome do Cliente", value="SOLLUM")
        cnpj_cliente = st.text_input("CNPJ / CPF do Cliente (Opcional)", value="09.503.092/0001-05")
        contato = st.text_input("Pessoa de Contato", value="Setor de Compras")

    with col2:
        forma_pagto = st.text_input("Forma de Pagamento", value="Boleto bancário 30 dias")
        prazo_entrega = st.text_input("Prazo de Entrega", value="Pronta entrega")
        tipo_frete = st.text_input("Tipo de Frete", value="A RETIRAR EM IMPERATRIZ")

    with col3:
        validade_dias = st.number_input("Validade em Dias", min_value=1, value=10)
        vendedor = st.text_input("Nome do Vendedor", value="Nataael Silveira")
        cargo_vendedor = st.text_input("Cargo", value="Departamento Comercial")
        cidade_data = st.text_input("Cidade e Data", value=f"Imperatriz - MA, {datetime.date.today().strftime('%d de %B de %Y')}")

    st.subheader("2. Itens do Orçamento")
    
    default_items = pd.DataFrame([
        {"Descrição": "Bainhas para Enxada", "Qtd": 30, "R$ Unit.": 27.00},
    ])
    
    edited_df = st.data_editor(
        default_items,
        num_rows="dynamic",
        column_config={
            "Descrição": st.column_config.TextColumn("Descrição do Produto / Serviço", width="large"),
            "Qtd": st.column_config.NumberColumn("Quantidade", min_value=1, default=1),
            "R$ Unit.": st.column_config.NumberColumn("Preço Unitário (R$)", format="R$ %.2f", default=0.0),
        },
        use_container_width=True
    )

    btn_gerar = st.form_submit_button("🚀 Gerar PDF do Orçamento", type="primary")

if btn_gerar:
    itens_processados = []
    total_geral = 0.0

    for idx, row in edited_df.iterrows():
        qtd = float(row.get("Qtd", 0) or 0)
        unit = float(row.get("R$ Unit.", 0) or 0)
        total_item = qtd * unit
        total_geral += total_item
        
        desc = row.get("Descrição")
        if desc and str(desc).strip():
            itens_processados.append({
                "item": idx + 1,
                "descricao": desc,
                "qtd": int(qtd),
                "unit": f"R$ {unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "total": f"R$ {total_item:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            })

    total_str = f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    dados_template = {
        "numero_orcamento": numero_orc,
        "cliente": cliente,
        "cnpj_cliente": cnpj_cliente,
        "contato": contato,
        "forma_pagto": forma_pagto,
        "prazo_entrega": prazo_entrega,
        "tipo_frete": tipo_frete,
        "validade_dias": validade_dias,
        "cidade_data": cidade_data,
        "vendedor": vendedor,
        "cargo_vendedor": cargo_vendedor,
        "itens": itens_processados,
        "total_geral": total_str
    }

    try:
        pdf_gerado = gerar_pdf_orcamento(dados_template)
        st.success("Orçamento gerado com sucesso!")
        
        nome_download = "Orcamento_Vale_do_Campo_" + str(numero_orc).replace("/", "_") + ".pdf"

        with open(pdf_gerado, "rb") as pdf_file:
            st.download_button(
                label="📥 Baixar Orçamento em PDF",
                data=pdf_file,
                file_name=nome_download,
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"Erro ao gerar o PDF: {e}")