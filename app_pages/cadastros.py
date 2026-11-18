import streamlit as st

from services.cadastros import (
    cadastrar_equipamento,
    cadastrar_modelo,
    listar_modelos_ativos,
)

from services.locais import (
    listar_locais_ativos,
)


# ============================================================
# CABEÇALHO
# ============================================================

st.title("Cadastros")

st.caption(
    "Cadastro de novos equipamentos "
    "e modelos do parque tecnológico."
)


# ============================================================
# MENSAGENS
# ============================================================

if "cadastro_equipamento_sucesso" in st.session_state:

    st.toast(
        st.session_state.pop(
            "cadastro_equipamento_sucesso"
        ),
        icon="✅",
    )


if "cadastro_modelo_sucesso" in st.session_state:

    st.toast(
        st.session_state.pop(
            "cadastro_modelo_sucesso"
        ),
        icon="✅",
    )


# ============================================================
# ABAS
# ============================================================

tab_equipamento, tab_modelo = st.tabs(
    [
        "🩺 Novo equipamento",
        "📋 Novo modelo",
    ]
)


# ============================================================
# CADASTRAR EQUIPAMENTO
# ============================================================

with tab_equipamento:

    st.subheader(
        "Cadastrar novo equipamento"
    )

    st.write(
        "Utilize este formulário quando uma nova "
        "unidade física entrar no parque tecnológico."
    )


    # --------------------------------------------------------
    # CARREGAR MODELOS
    # --------------------------------------------------------

    try:

        modelos = (
            listar_modelos_ativos()
        )

    except Exception as erro:

        st.error(
            "Não foi possível carregar "
            "os modelos cadastrados."
        )

        st.exception(erro)

        modelos = []


    # --------------------------------------------------------
    # CARREGAR LOCAIS
    # --------------------------------------------------------

    try:

        locais = (
            listar_locais_ativos()
        )

    except Exception as erro:

        st.error(
            "Não foi possível carregar "
            "os locais cadastrados."
        )

        st.exception(erro)

        locais = []


    # --------------------------------------------------------
    # VALIDAR MODELOS
    # --------------------------------------------------------

    if not modelos:

        st.warning(
            "Ainda não existem modelos ativos cadastrados. "
            "Cadastre primeiro um modelo na aba "
            "'Novo modelo'."
        )

    else:

        # ----------------------------------------------------
        # OPÇÕES DE MODELO
        # ----------------------------------------------------

        opcoes_modelo = {}


        for modelo in modelos:

            tipo = (
                modelo.get("tipo")
                or "Equipamento"
            )

            fabricante = (
                modelo.get("fabricante")
                or "-"
            )

            nome_modelo = (
                modelo.get("modelo")
                or "-"
            )


            texto = (
                f"{tipo} — "
                f"{fabricante} — "
                f"{nome_modelo}"
            )


            opcoes_modelo[
                texto
            ] = modelo


        # ----------------------------------------------------
        # OPÇÕES DE LOCAL
        # ----------------------------------------------------

        opcoes_local = {
            "Sem local definido":
                None
        }


        for local in locais:

            setor = (
                local.get("setor")
                or "Setor não informado"
            )

            sala = (
                local.get("sala")
                or "Sala não informada"
            )

            codigo = (
                local.get("codigo")
                or "-"
            )


            texto = (
                f"{setor} — "
                f"{sala} "
                f"({codigo})"
            )


            opcoes_local[
                texto
            ] = local["id"]


        # ----------------------------------------------------
        # FORMULÁRIO
        # ----------------------------------------------------

        with st.form(
            "form_cadastrar_equipamento"
        ):

            modelo_selecionado = (
                st.selectbox(
                    "Modelo *",
                    options=list(
                        opcoes_modelo.keys()
                    ),
                )
            )


            modelo_dados = (
                opcoes_modelo[
                    modelo_selecionado
                ]
            )


            periodicidade = (
                modelo_dados.get(
                    "periodicidade_preventiva_meses"
                )
            )


            criticidade_padrao = (
                modelo_dados.get(
                    "criticidade_padrao"
                )
            )


            if periodicidade:

                st.caption(
                    f"Periodicidade preventiva do modelo: "
                    f"{periodicidade} mês(es)."
                )


            if criticidade_padrao:

                st.caption(
                    f"Criticidade padrão do modelo: "
                    f"{criticidade_padrao}."
                )


            patrimonio = st.text_input(
                "Patrimônio",
                placeholder=(
                    "Ex.: 123456"
                ),
            )


            numero_serie = st.text_input(
                "Número de série",
                placeholder=(
                    "Ex.: SN-A12345"
                ),
            )


            col_data1, col_data2 = (
                st.columns(2)
            )


            with col_data1:

                data_aquisicao = (
                    st.date_input(
                        "Data de aquisição",
                        value=None,
                        format="DD/MM/YYYY",
                    )
                )


            with col_data2:

                data_instalacao = (
                    st.date_input(
                        "Data de instalação",
                        value=None,
                        format="DD/MM/YYYY",
                    )
                )


            local_selecionado = (
                st.selectbox(
                    "Local inicial",
                    options=list(
                        opcoes_local.keys()
                    ),
                )
            )


            # Por padrão, a unidade herda a
            # criticidade definida no modelo.

            criticidade = (
                criticidade_padrao
            )


            observacoes = st.text_area(
                "Observações",
                placeholder=(
                    "Informações adicionais "
                    "sobre o equipamento "
                    "(opcional)"
                ),
                height=100,
            )


            confirmar_equipamento = (
                st.form_submit_button(
                    "Cadastrar equipamento",
                    type="primary",
                    use_container_width=True,
                )
            )


        # ----------------------------------------------------
        # SALVAR EQUIPAMENTO
        # ----------------------------------------------------

        if confirmar_equipamento:

            local_id = (
                opcoes_local[
                    local_selecionado
                ]
            )


            try:

                equipamento_criado = (
                    cadastrar_equipamento(
                        modelo_id=(
                            modelo_dados["id"]
                        ),

                        patrimonio=patrimonio,

                        numero_serie=(
                            numero_serie
                        ),

                        data_aquisicao=(
                            data_aquisicao
                        ),

                        data_instalacao=(
                            data_instalacao
                        ),

                        local_atual_id=(
                            local_id
                        ),

                        criticidade=(
                            criticidade
                        ),

                        observacoes=(
                            observacoes
                        ),
                    )
                )


                codigo = None


                if equipamento_criado:

                    codigo = (
                        equipamento_criado[
                            0
                        ].get(
                            "codigo"
                        )
                    )


                if codigo:

                    mensagem = (
                        "Equipamento cadastrado "
                        "com sucesso. "
                        f"Código: {codigo}"
                    )

                else:

                    mensagem = (
                        "Equipamento cadastrado "
                        "com sucesso."
                    )


                st.session_state[
                    "cadastro_equipamento_sucesso"
                ] = mensagem


                st.rerun()


            except Exception as erro:

                st.error(
                    "Não foi possível cadastrar "
                    "o equipamento."
                )

                st.exception(
                    erro
                )


# ============================================================
# CADASTRAR MODELO
# ============================================================

with tab_modelo:

    st.subheader(
        "Cadastrar novo modelo"
    )

    st.write(
        "Cadastre um modelo apenas uma vez. "
        "Depois, diferentes unidades físicas "
        "podem utilizar o mesmo modelo."
    )


    # --------------------------------------------------------
    # FORMULÁRIO
    # --------------------------------------------------------

    with st.form(
        "form_cadastrar_modelo"
    ):

        tipo = st.text_input(
            "Tipo de equipamento *",
            placeholder=(
                "Ex.: Monitor multiparamétrico"
            ),
        )


        fabricante = st.text_input(
            "Fabricante *",
            placeholder=(
                "Ex.: Philips"
            ),
        )


        modelo = st.text_input(
            "Modelo *",
            placeholder=(
                "Ex.: IntelliVue MX450"
            ),
        )


        possui_preventiva = (
            st.checkbox(
                "Modelo possui periodicidade "
                "de manutenção preventiva"
            )
        )


        periodicidade = None


        if possui_preventiva:

            periodicidade = (
                st.number_input(
                    "Periodicidade preventiva "
                    "(meses) *",
                    min_value=1,
                    step=1,
                    value=12,
                )
            )


        fonte_periodicidade = (
            st.text_input(
                "Fonte da periodicidade",
                placeholder=(
                    "Ex.: Manual do fabricante"
                ),
            )
        )


        referencia_documental = (
            st.text_input(
                "Referência documental",
                placeholder=(
                    "Ex.: Manual de serviço, "
                    "seção 8.2"
                ),
            )
        )


        criticidade_padrao = (
            st.text_input(
                "Criticidade padrão",
                placeholder=(
                    "Ex.: ALTA"
                ),
            )
        )


        confirmar_modelo = (
            st.form_submit_button(
                "Cadastrar modelo",
                type="primary",
                use_container_width=True,
            )
        )


    # --------------------------------------------------------
    # SALVAR MODELO
    # --------------------------------------------------------

    if confirmar_modelo:

        if not tipo.strip():

            st.warning(
                "Informe o tipo "
                "do equipamento."
            )

        elif not fabricante.strip():

            st.warning(
                "Informe o fabricante."
            )

        elif not modelo.strip():

            st.warning(
                "Informe o modelo."
            )

        else:

            try:

                cadastrar_modelo(
                    tipo=tipo,
                    fabricante=fabricante,
                    modelo=modelo,
                    periodicidade_preventiva_meses=(
                        int(periodicidade)
                        if periodicidade
                        else None
                    ),
                    fonte_periodicidade=(
                        fonte_periodicidade
                    ),
                    referencia_documental=(
                        referencia_documental
                    ),
                    criticidade_padrao=(
                        criticidade_padrao
                    ),
                )


                st.session_state[
                    "cadastro_modelo_sucesso"
                ] = (
                    "Modelo cadastrado "
                    "com sucesso."
                )


                st.rerun()


            except ValueError as erro:

                st.warning(
                    str(erro)
                )


            except Exception as erro:

                st.error(
                    "Não foi possível "
                    "cadastrar o modelo."
                )

                st.exception(
                    erro
                )


    # --------------------------------------------------------
    # MODELOS JÁ CADASTRADOS
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        "#### Modelos ativos cadastrados"
    )


    try:

        modelos_cadastrados = (
            listar_modelos_ativos()
        )


        if modelos_cadastrados:

            linhas = []


            for item in modelos_cadastrados:

                linhas.append(
                    {
                        "Tipo":
                            item.get(
                                "tipo"
                            )
                            or "-",

                        "Fabricante":
                            item.get(
                                "fabricante"
                            )
                            or "-",

                        "Modelo":
                            item.get(
                                "modelo"
                            )
                            or "-",

                        "Preventiva":
                            (
                                f"{item.get('periodicidade_preventiva_meses')} meses"
                                if item.get(
                                    "periodicidade_preventiva_meses"
                                )
                                else "-"
                            ),

                        "Criticidade":
                            item.get(
                                "criticidade_padrao"
                            )
                            or "-",
                    }
                )


            st.dataframe(
                linhas,
                hide_index=True,
                width="stretch",
            )


        else:

            st.info(
                "Nenhum modelo cadastrado."
            )


    except Exception as erro:

        st.error(
            "Não foi possível carregar "
            "os modelos existentes."
        )

        st.exception(
            erro
        )