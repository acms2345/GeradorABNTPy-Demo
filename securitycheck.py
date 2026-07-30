from urllib.parse import urlparse
import ipaddress
import socket
import requests

class urlInseguraErro(Exception):
    pass

class tipoConteudoErro(Exception):
    pass

class redeSiteErro(Exception):
    pass

class conteudoGrandeDemaisErro(Exception):
    pass


def verificarURL(url: str):
    """A presente função verifica alguns quesitos de segurança na URL solicitada,
    como redirecionamentos maliciosos, IPs não autorizados para acesso e etc."""
    parseurl = urlparse(url)
    
    if parseurl.scheme not in ['http', 'https']:
        raise urlInseguraErro("Formato de link inválido (não usa HTTP ou HTTPS).")


    #Verificação de IP's

    hostname = parseurl.hostname

    try:

        ip = socket.gethostbyname(hostname)
        enderecoip = ipaddress.ip_address(ip)

        if enderecoip.is_loopback or enderecoip.is_private or enderecoip.is_reserved or enderecoip.is_multicast or enderecoip.is_link_local:
            raise urlInseguraErro(f"Tentativa de acesso a IP não autorizado: {ip}")

    except socket.gaierror:
        raise urlInseguraErro("Hostname inválido ou que não resolve.")



MAXIMO_REDIRECTS = 5
LIMITE_CONTENT_LENGTH = 3000000

def buscarUrlSegura(url: str):
    """Essa função coleta a url, faz todas as verificações de segurança
    e devolve o exato valor para ser usado pelo Beautiful Soup."""

    try: 
        verificarURL(url)
    except urlInseguraErro as erro:
        raise erro

    headers = {
            "User-Agent": "Mozilla/5.0"
     } 

    try:
        doc = requests.get(url, timeout=15, stream=True, allow_redirects=False, headers=headers)
    except requests.exceptions.RequestException as erro:
        raise redeSiteErro(f"Falha no acesso à url: {erro}")

    if doc.status_code in (200, 301, 302, 303, 307, 308):
    
        #Se for tentativa de redirecionamento... Inspecionar para onde redireciona
        contador = 0
        while doc.status_code in (301, 302, 303, 307, 308):
            contador+=1

            if contador > MAXIMO_REDIRECTS:
                raise urlInseguraErro("Muitos redirecionamentos.")

            proximaUrl = doc.headers.get("Location")

            try: verificarURL(url)
            except urlInseguraErro as erro:
                raise erro
            
            doc = requests.get(proximaUrl, timeout=15, allow_redirects=False, headers=headers)

    contenttype = doc.headers.get('Content-Type', "")

    if not (contenttype.startswith("text/html")):
        raise tipoConteudoErro(f"Content-type incompatível: {contenttype}")

    content_length = doc.headers.get('Content-Length')

    if content_length and int(content_length) > LIMITE_CONTENT_LENGTH:
        raise conteudoGrandeDemaisErro("Content-length grande demais.")

    #O código a seguir faz a coleta do conteúdo da URL
    # (e impede que esse passe do tamanho limite).
    conteudo = b""

    for pedaco in doc.iter_content(chunk_size=8192):
        conteudo += pedaco

        if len(conteudo) > LIMITE_CONTENT_LENGTH:
            raise conteudoGrandeDemaisErro("O limite de tamanho foi excedido.")


    return conteudo