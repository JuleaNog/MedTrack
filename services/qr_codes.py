from io import BytesIO
from urllib.parse import urlencode

import qrcode


APP_URL = "https://medtrack.streamlit.app"


def gerar_url_equipamento(codigo: str) -> str:
    """
    Gera a URL permanente correspondente ao equipamento.
    """

    parametros = urlencode(
        {
            "equipamento": codigo
        }
    )

    return f"{APP_URL}/?{parametros}"


def gerar_qr_equipamento(codigo: str) -> tuple[bytes, str]:
    """
    Gera o QR Code em PNG e retorna:
    - conteúdo da imagem em bytes
    - URL codificada no QR
    """

    url = gerar_url_equipamento(codigo)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(url)

    qr.make(fit=True)

    imagem = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer = BytesIO()

    imagem.save(
        buffer,
        format="PNG",
    )

    buffer.seek(0)

    return buffer.getvalue(), url