from geradorabnt.core import citacaoInLine, citacaoRef, limparPasta

import securitycheck

from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware

from bs4 import BeautifulSoup

import requests

from pydantic import BaseModel

from uuid import uuid4



class linkCitacao(BaseModel):
    link: str

app = FastAPI()

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


@app.post("/citar-link")
def processamentoLink(link: linkCitacao):
    headers = {
        "User-Agent": "Mozilla/5.0"
    } 
    pasta = uuid4()
    try:

        conteudo = securitycheck.buscarUrlSegura(link.link)
        soup = BeautifulSoup(conteudo.content, 'html.parser')
        citacaoEmTexto = citacaoInLine(soup, link.link, pasta)
        refBibliografica = citacaoRef(pasta, link.link)

        return {"citacaoInLine": citacaoEmTexto, "citacaoRef" : refBibliografica}

    #Exceções de segurança:
    except securitycheck.urlInseguraErro as erro:
        raise HTTPException(400, detail=erro)
    except securitycheck.tipoConteudoErro as erro:
        raise HTTPException(415, detail=erro)

    #Exceções de erro ao criar a citação:
    except (TypeError, AttributeError, KeyError) as erro:
        raise HTTPException(status_code=422, detail=f"Não foi possível formar a citação por essa página: {erro}")

    #Outras exceções:
    except requests.exceptions.MissingSchema:
        raise HTTPException(
            status_code=502,
            detail="O usuário não inseriu 'http:// ou https://'"
        )

    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível acessar o site."
        )
    finally:
        limparPasta(pasta)


    



