from geradorabnt import citacaoInLine, citacaoRef, limparPasta

import securitycheck

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request

from bs4 import BeautifulSoup

from pydantic import BaseModel

from uuid import uuid4

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from citeproc import formatter


class linkCitacao(BaseModel):
    link: str

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

#Domínios permitidos
origins = [
    "https://acms2345.github.io",
    "https://acms.me",
]

# Uso do CORS Middleware para validar os domínios e métodos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],

)

@app.get('/')
def healthforRender():
    return {"status": "ok"}


@app.post("/citar-link")
@limiter.limit("10/minute")
def processamentoLink(link: linkCitacao, request: Request):
    headers = {
        "User-Agent": "Mozilla/5.0"
    } 
    pasta = uuid4()
    try:

        conteudo = securitycheck.buscarUrlSegura(link.link)
        soup = BeautifulSoup(conteudo, 'html.parser')
        citacaoEmTexto = citacaoInLine(soup, link.link, pasta, formatador=formatter.html)
        refBibliografica = citacaoRef(pasta, link.link)

        return {"citacaoInLine": citacaoEmTexto, "citacaoRef" : refBibliografica}

    #Exceções de segurança:
    except securitycheck.urlInseguraErro as erro:
        raise HTTPException(400, detail=str(erro))
    except securitycheck.tipoConteudoErro as erro:
        raise HTTPException(415, detail=str(erro))
    except securitycheck.redeSiteErro as erro:
        raise HTTPException(502, detail=str(erro))
    except securitycheck.conteudoGrandeDemaisErro as erro:
        raise HTTPException(413, detail=str(erro))

    #Exceções de erro ao criar a citação:
    except (TypeError, AttributeError, KeyError, ValueError) as erro:
        raise HTTPException(status_code=422, detail=f"Não foi possível formar a citação por essa página: {erro}")

    finally:
        limparPasta(pasta)


    



