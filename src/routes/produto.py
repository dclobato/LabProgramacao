from flask import Blueprint, render_template, flash, redirect, url_for, request, Response
from flask_login import login_required

from src.forms.produto import NovoProdutoForm
from src.models.categoria import Categoria
from src.models.produto import Produto
from src.modules import db
from src.utils import get_tuples, b64encode_image, b64decode_image

bp = Blueprint("produto", __name__, url_prefix="/produto")


@bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    form = NovoProdutoForm()
    form.categoria.choices = get_tuples(Categoria, db)

    if form.validate_on_submit():
        categoria = db.session.get(Categoria, form.categoria.data)
        if categoria is None:
            flash("Categoria inválida", category='info')
            return redirect(url_for("index"))

        produto = Produto()
        produto.nome = form.nome.data
        produto.preco = form.preco.data
        produto.ativo = form.ativo.data
        produto.categoria = categoria
        if form.foto_raw.data:
            produto.possui_foto = True
            produto.foto_base64 = b64encode_image(request.files[form.foto_raw.name].read())
            produto.foto_mime = request.files[form.foto_raw.name].mimetype
        else:
            produto.possui_foto = False
            produto.foto_base64 = None
            produto.foto_mime = None
        db.session.add(produto)
        db.session.commit()
        flash(message=f"Produto '{form.nome.data}' adicionado", category="success")
        return redirect(url_for("index"))
    return render_template("render_simple_form.jinja",
                           title="Nova categoria",
                           form=form)


@bp.route("/<uuid:id_produto>/imagem", methods=["GET"])
@login_required
def imagem(id_produto):
    produto = db.session.get(Produto, id_produto)
    if produto is None:
        return Response(status=404)
    if produto.possui_foto and produto.foto_base64:
        return Response(b64decode_image(produto.foto_base64), mimetype=produto.foto_mime)
    if not produto.possui_foto:
        # https://placeholderimage.dev/
        return Response(b64decode_image("iVBORw0KGgoAAAANSUhEUgAAAZAAAAGQCAYAAACAvzbMAAAAAXNSR0IArs4c6QAAHdNJREFUeF7t3"
                                        "XeIfGfVB/AngqLGiEZiiy2xxN4CsQVLwNiIijH6hz1RFLFE7L13rNGoRImoMZZEjCWighohlhhFjb"
                                        "3FLgoGu6JoXs6F2Xd2fnd3Z57d2T1n8rnw8hJ/88yc+Zxn73du3+/888+/uFkIECBAgMCCAvsJkAX"
                                        "FvJwAAQIEBgEBYiIQIECAQJeAAOliM4gAAQIEBIg5QIAAAQJdAgKki80gAgQIEBAg5gABAgQIdAkI"
                                        "kC42gwgQIEBAgJgDBAgQINAlIEC62AwiQIAAAQFiDhAgQIBAl4AA6WIziAABAgQEiDlAgAABAl0CA"
                                        "qSLzSACBAgQECDmAAECBAh0CQiQLjaDCBAgQECAmAMECBAg0CUgQLrYDCJAgAABAWIOECBAgECXgA"
                                        "DpYjOIAAECBASIOUCAAAECXQICpIvNIAIECBAQIOYAAQIECHQJCJAuNoMIECBAQICYAwQIECDQJSB"
                                        "AutgMIkCAAAEBYg4QIECAQJeAAOliM4gAAQIEBIg5QIAAAQJdAgKki80gAgQIEBAg5gABAgQIdAkI"
                                        "kC42gwgQIEBAgJgDBAgQINAlIEC62AwiQIAAAQFiDhAgQIBAl4AA6WIziAABAgQEiDlAgAABAl0CA"
                                        "qSLzSACBAgQECDmAAECBAh0CQiQLjaDCBAgQECAmAMECBAg0CUgQLrYDCJAgAABAWIOECBAgECXgA"
                                        "DpYjOIAAECBASIOUCAAAECXQICpIvNIAIECBAQIOYAAQIECHQJCJAuNoMIECBAQICYAwQIECDQJSB"
                                        "AutgMIkCAAAEBYg4QIECAQJeAAOliM4gAAQIEBIg5QIAAAQJdAgKki80gAgQIEBAg5gABAgQIdAkI"
                                        "kC42gwgQIEBAgJgDBAgQINAlIEC62AwiQIAAAQFiDhAgQIBAl4AA6WIziAABAgQEiDlAgAABAl0CA"
                                        "qSLzSACBAgQECDmAAECBAh0CQiQLjaDCBAgQECAmAMECBAg0CUgQLrYDCJAgAABAWIOECBAgECXgA"
                                        "DpYjOIAAECBASIOUCAAAECXQICpIvNIAIECBAQIOYAAQIECHQJCJAuNoMIECBAQICYAwQIECDQJSB"
                                        "AutgMIkCAAAEBYg4QIECAQJeAAOliM4gAAQIEBIg5QIAAAQJdAgKki80gAgQIEBAg5gABAgQIdAkI"
                                        "kC42gwgQIEBAgJgDBAgQINAlIEC62AwiQIAAAQFiDhAgQIBAl4AA6WIziAABAgQEiDlAgAABAl0CA"
                                        "qSLzSACBAgQECDmAAECBAh0CQiQLjaDCBAgQECAmAMECBAg0CUgQLrYDCJAgAABAWIOECBAgECXgA"
                                        "DpYjOIAAECBASIOUCAAAECXQICpIvNIAIECBAQIOYAAQIECHQJCJAuNoMIECBAQICYAwQIECDQJSB"
                                        "AutgMIkCAAAEBYg4QIECAQJeAAOliM4gAAQIEBIg5QIAAAQJdAgKki80gAgQIEBAg5gABAgQIdAkI"
                                        "kC42gwgQIEBAgJgDBAgQINAlIEC62AwiQIAAAQFiDhAgQIBAl4AA6WIziAABAgQEiDlAgAABAl0CA"
                                        "qSLzSACBAgQECDmAAECBAh0CQiQLjaDCBAgQECAmAMECBAg0CUgQLrYDCJAgAABAWIOECBAgECXgA"
                                        "DpYjOIAAECBASIOUCAAAECXQICpIvNIAIECBAQIOYAAQIECHQJCJAuNoMIECBAQICYAwQIECDQJSB"
                                        "AutgMIkCAAAEBYg4QIECAQJeAAOliM4gAAQIEBIg5QIAAAQJdAgKki80gAgQIEBAg5gABAgQIdAkI"
                                        "kC42gwgQIEBAgJgDBAgQINAlIEC62AwiQIAAAQFiDhAgQIBAl4AA6WIziAABAgQEiDlAgAABAl0CA"
                                        "qSLzSACBAgQECDmAAECBAh0CQiQLjaDCBAgQECAmAMECBAg0CUgQLrYDCJAgAABAWIOECBAgECXgA"
                                        "DpYjOIAAECBASIOUCAAAECXQICpIvNIAIECBAQIOYAAQIECHQJCJAuNoMIECBAQICYAwQIECDQJSB"
                                        "AutgMIkCAAAEBYg4QIECAQJeAAOliM4gAAQIEBIg5QIAAAQJdAgKki80gAgQIEBAg5gABAgQIdAkI"
                                        "kC42gwgQIEBAgJgDBAgQINAlIEC62AwiQIAAAQFiDhAgQIBAl4AA6WIziAABAgQEiDlAgAABAl0CA"
                                        "qSLzSACBAgQECDmAAECBAh0CQiQLjaDCBAgQECAmAMECBAg0CUgQLrYDCJAgAABAWIOECBAgECXgA"
                                        "DpYjOIAAECBASIOUCAAAECXQICpIvNIAIECBAQIOYAAQIECHQJCJAuNoMIECBAQICYAwQIECDQJSB"
                                        "AutgMIkCAAAEBYg4QIECAQJeAAOliM4gAAQIEBIg5QIAAAQJdAgKki80gAgQIEBAg5gABAgQIdAkI"
                                        "kC42gwgQIEBAgJgDBAgQINAlIEC62AwiQIAAAQGyYnPgla98ZTvzzDO7v9XlL3/5ds1rXrMdcMAB7"
                                        "YY3vGG79a1v3W5/+9u3K17xit3vueoD//a3v7UXvehF7Qtf+MLaV33Sk57UHv7wh6/6V/f9LuECAm"
                                        "TFJsB2A2SM4wpXuEI76qij2qMf/eghXCzrBSoFyD//+c92xhlntOtf//rtjne8o1YS2JaAANkWX77"
                                        "BywiQybe82tWu1h772Me2Y445pu233375vvweVVQhQC6++OL2la98pZ1yyint29/+dnvNa14z/Ciw"
                                        "ENiOgADZjl7CscsMkPi6V7nKVdpTn/rUdvTRRyf89ntTUvYAifre+MY3ts985jPtH//4x4AkQPZmr"
                                        "qzapwqQFevobIAcfPDB7WlPe1q70Y1uNNc3/e9//9t+9rOftV//+tfDCid+rc4uhx12WHvZy17WDj"
                                        "nkkLnec9VflD1Afv/737enP/3p7Xvf+95aKwTIqs/K3fl+AmR3nHftU2YD5FrXulZ7yUte0m55y1s"
                                        "uXMP//ve/dtZZZ7W3v/3t7Y9//OO68XGA+IlPfKJdWa01AbLw1DJgRQQEyIo0cvI1djJA4j1j3/n7"
                                        "3ve+Yd/5ZPdH/O83uclN2stf/vJ2netcZ8UEF/86AmRxMyNWQ0CArEYf177FTgdIvPHYCjJO941TV"
                                        "x2ItQWyYn9Cvs4CAgJkAawKL11GgMT3jmtL4r2nlyc84QntkY98ZAWWpdZoC2SpvN48sYAASdycnt"
                                        "KWFSBf+tKX2gte8IL2pz/9aa2sY489tj372c/uKXOlxgiQlWqnL7OAgABZAKvCS5cVIHE2VgRInJ0"
                                        "1WcYCZPaMn5ve9Kbtta99bYtrSH7729+20047rUUY/epXv2pxgeKNb3zjdqc73WnYFRZnjG22/OY3"
                                        "vxmu9j7vvPPaL3/5y+E9YplcPR/HZe5whzsM77f//vtvq10XXXRRO+ecc4bPm/6sa1/72sNxn7vf/"
                                        "e7tbne72/A5iwTI2GsXDeLZXoydKPG5z32uPeMZz5jbYN4a/v73v7dzzz23ffnLX27f//73h55Ojo"
                                        "1NbI444oh217vedct+zl2cF6YVECBpW9NX2LICZN4tkI0C5Kc//Wl7/etf337+85+PfrEImle84hU"
                                        "tVoazy49+9KN28sknt2984xvrDuRvJBRhdZ/73Kc99KEPXfgWLHGldpw08NGPfrTFd9lsue51r9tO"
                                        "OOGEduSRRw5nus1zK5OqAfKXv/ylnXrqqe3ss8/e54y8MaMI9bjS/fjjj5/7FPK+GW/UXgoIkL3UX"
                                        "8JnLytAxo6BjN3vaSxAHvGIR7S3ve1tG4ZHMDzucY8bbpUyvfz73/9uH/zgB4cV+uxpxPPQxanLcd"
                                        "HjzW52s3lePvyaDr/4dT3vEivKe9zjHu0Pf/jD8Mt8smx0L6yKAfLVr361vfWtb113Hcm8PhHm0f/"
                                        "jjjvOKd/zohV6nQAp1Kx5Sl1GgMSv8viF/dnPfnathCtd6UrD/zZ7P6XZAIkr1y93ucut7fqK/77V"
                                        "rW7VrnrVqw4r3e9+97vDv8eFibE7a7JEeLzlLW8ZtgSmTx+Of49dX4ceeuhws8dLX/rSLX4dX3DBB"
                                        "Wu7tKadrne967XnPe95w00hN1tid9iLX/zi9s1vfnOfl8VFmFFbhMVmnzU9cK8D5He/+91gEkuE1v"
                                        "vf//51AR5bBje4wQ3WSj7ooIPabW5zm32+e/Q8rmIf2xqLHoRL3GjzP//5T/vBD37QLrzwwn36FW6"
                                        "Pecxjhi1Ct8CZ56+4zmsESJ1ezVXpMgLkE5/4xHDri+kV+W1ve9thpR9BML2MXfU8+fd73/veLc7c"
                                        "mh4T4fSd73xnWMFHGMSy0bUnERz3v//9h7vcHnjgges+N8bEyv+d73xni1/M00u89wtf+MIW++jHl"
                                        "girV73qVe1jH/vYun+OLZhY8cXdiKdXfHGBZWylvOMd79jwV/leB8hWPZnnSvTwjB7P7naMHw2xxR"
                                        "jHnGYDIfr/3ve+d7Ccni9ugTPXn2+5FwmQci3bvOCdDJDNrkQf2+UUlW0UILHSietGZlf8Y9/mhz/"
                                        "84XDAPo6bTJY4NnLiiScOB2c3W+Ig75ve9Kb2kY98ZN3L7nvf+7ZnPetZ7TKXucw+w7/4xS8OW1PT"
                                        "Z5jFQf04w+zKV77yhh8XWy1xMeX555+/z2uqB0gEexyT+tSnPrX23WJL4sEPfvAQqmOOkxdGmH/84"
                                        "x8fdntN73p0C5wVW9m01gTIivV0uwHy5z//ucXuj7hza6xYx+6FFVsfEQZjt3YfC5BY8cTKO7ZAtl"
                                        "pi5RMBEMc9JkvsLov7ed3znvfcavjw77GbKX45x5lIkyV+AUcoxRla08vY7rnY8ojvN89V9mNhF+9"
                                        "fPUDGQjWOYzzlKU/ZNDymQ2TsDgZugTPXFC7zIgFSplXzFbrsu/FudUxhLEDiGELUFWctbbXEKbPP"
                                        "fe5zh1NEJ8u97nWv9pznPGc4VjLvMnbacawA49TW6d0usd8+jpFM76ZZ9GFQsdss7hc2vVQOkDie8"
                                        "epXv3o4/jRZ4vkhsZUWWxHzLmMnDMQJDbG78BrXuMa8b+N1iQUESOLm9JS2zACZZzfSWIDE7qD4RR"
                                        "9bIlstsdUQr53sP++9ZUqsBGMXTOxKmSyHH3748L/F1shkmT27LAJy9oD+VjUvEkK7dRbWdM2L3o0"
                                        "3tkBjizFOcJgsY+G7lUv8+yc/+cnh+NNk2ejki3ney2vyCQiQfD3ZVkXLCJBYicdFc/Ewqa2eSDi2"
                                        "spr3IrX44u9+97uHs68myyJbL7Nws+EQFyrGr+g4C2yyxMHkD33oQ2v/fec733k4Gyse6Tvv8te//"
                                        "nVYScZun8lSeQvkW9/61rC7Ly7cnCxhEtfWLLrENTyxhRePCJgsboGzqGLe1wuQvL3pqmynAiTOWI"
                                        "rTZCdXds+ebbVRcWMBssguodn646B5bJHEGViLLl/72teGFXucLjwdGJMbQI5tDTzgAQ8YDp4verr"
                                        "pbN2VA2T2KvbtPBIgTkx4/vOfv+7amkV+UCzac6/fXQEBsrveS/+07T5QKk6ljTOPFl2BTr7YdgJk"
                                        "J1foUc/YcZAIh1iBxTK2cnvQgx600C1AJt97dsupcoC85z3vaW9+85vX5mqcrhvHRLba+hyb3GM9j"
                                        "QsvI1Que9nLLv3vwQcsV0CALNd31999u2dhbbfgnQ6Q7fxa3aqWrf59EYvZle4qBcj0/cwWMZm8di"
                                        "e3Kns+35jlCQiQ5dnuyTsLkP9nj1uTPPOZz1x3Rtf0il2AHDU6R2fDcDsBEqdlx5ycvi5nO7sl9+S"
                                        "PyoduKCBAVmxyrFqA9B6T2GgXVvjEnXR3ehfWKm+B7PQurO30dMX+XMt/HQFSvoXrv0DlAIlvspO7"
                                        "O8buIDx9C484VTgO0E9fcHjMMccM15xMbqsy7/SIix/jFh6TZZm7sGZPDtjqIPeip/Hu5EH0uBI9P"
                                        "L/+9a+v2Wxnt+S8/fC63REQILvjvGufUj1Alnka79iKdvY03jjr7KUvfWmL6xXmXf71r38NYz796U"
                                        "/vSoDEDQ6nH+S10wGy7NN4Fzkrb94eeN3eCAiQvXFf2qdWD5DdvpBw9kK3q1/96sO1InG7lnmXsav"
                                        "nN1pJjm31LPqLPG7ieMopp6yVt9MB4kLCeTvvdQJkxeZA9QDZ7VuZ/OIXvxh+zccFb5Mlbjv+5Cc/"
                                        "ee5TmcfuVrzZr+zZHi1y8WLc5ytOgZ1+9shOB4hbmazYSmGJX0eALBF3L966eoAs62aKsUsqrq6Ol"
                                        "fX0EivLN7zhDeuuRo8VclyAOPZ8jNmebvQckc0CZPZ4ySJbPWecccZwjcb0rdJ3OkDiOy7rZoqLhv"
                                        "Ne/A35zPkFBMj8ViVeWT1AAnnsDrfxZLvYKogzqDa7yDHurnvSSSetC4R4z81uyBjPI4mD6dM3VIw"
                                        "78sb9oOJWKhstY3f9nbx2swCZ3U0XY+Lq+LjlRzycaWyJYI1jLBF2s09n7AmQ6Qsqxz5vo9u53+9+"
                                        "92uPf/zjN72x5Ua19tyQscQf3SW4SAGyYs1fhQDpfaBU3ME37oobZ19NL3GDxAiIm9/85huunMduP"
                                        "R4r5njM7tFHH73uFuZRXzyfPY5FxP8fWzYLkLHddPEet7vd7YZniMeWz6UudanhbeOZLBGop59++v"
                                        "DM9djymH3K41YBMnbF/eRxv3GNx0aB3PNAqYsuuqjFKc1xJ9+4Cn2yxP3U4l5qD3nIQ1bsL+6S/XU"
                                        "EyIr1fxUCJFqy2SNtY2V0yCGHDI9T3eqRtvPcQXjyebFr6AMf+MA+MyK2fuI25HE/sFiBx913p4+Z"
                                        "xIDYRTb9QKqtzjQ67bTThgCafVxvvFd8XoREBFXcx2t6iyO+e1xHESvnye3WtwqQsbPEZr/kRndM3"
                                        "uyRtnG/tFvc4hZzPdJ2ngdRrdif4iXi6wiQFWvzqgTIZKUeWwbxi3b61+y8LYtf2bHba/ruu5uNjd"
                                        "02J598cjvrrLNGV+wbjY0tlFiZvutd71p7yVYBEgG5UWBt9DkRHvFI37ib7ete97oWdxuOZasAide"
                                        "MHTuZ/pywiud0jN00Mx7fG89Fn35C5Lw9iDB82MMe1uIeY5OtqnnHel1+AQGSv0cLVbhKATL54vFr"
                                        "P1bssbto7Bf7LFDctv2BD3zg8H+LPIQq3mey/z6uR/nJT36yqX3cIThWjI961KPahz/84XU3INwqQ"
                                        "CYBGePidvLTt04f+9B4GNcJJ5wwPJUxVsTTfZ4nQDbboovPi6cvxnNQYpfW2BLHe0499dR29tln73"
                                        "MMZuz1YRNbNbELsOcmjAtNei/eMwEBsmf0y/ngVQyQyYo9zng655xzhluDx7UK8d+xxMoqVoCx8jv"
                                        "yyCPbEUccMddjVzfrQKxwzzvvvPb5z3++XXDBBWvPs4hdS4ceeuhwnUg8ojfCKpZ5b2Uy9pnxHPf4"
                                        "nDjz6cc//vHa94qtmvheceJAPI9l//33Xxu+aIDEwDieEp8RB+NjN9zEL/4ttm4iQGbPUputN4IkH"
                                        "ncc9V544YUt7jc2CfVwieNNcTHmXe5yl3bggQcuZ5J71zQCAiRNKxRCgACBWgICpFa/VEuAAIE0Ag"
                                        "IkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa"
                                        "/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRC"
                                        "gACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAg"
                                        "TQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAg"
                                        "KkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0"
                                        "rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RL"
                                        "gACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAg"
                                        "VoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0Ag"
                                        "IkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa"
                                        "/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRC"
                                        "gACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAg"
                                        "TQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAg"
                                        "KkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0"
                                        "rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RL"
                                        "gACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAg"
                                        "VoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0Ag"
                                        "IkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa"
                                        "/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRC"
                                        "gACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAg"
                                        "TQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAg"
                                        "KkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0"
                                        "rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RL"
                                        "gACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAg"
                                        "VoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0Ag"
                                        "IkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa"
                                        "/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRC"
                                        "gACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAg"
                                        "TQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAg"
                                        "KkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0"
                                        "rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RL"
                                        "gACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0AgIkTSsUQoAAg"
                                        "VoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa/VEuAAIE0Ag"
                                        "IkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRCgACBWgICpFa"
                                        "/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAgTQCAiRNKxRC"
                                        "gACBWgICpFa/VEuAAIE0AgIkTSsUQoAAgVoCAqRWv1RLgACBNAICJE0rFEKAAIFaAgKkVr9US4AAg"
                                        "TQC/wfC2WMxwTThTQAAAABJRU5ErkJggg=="), mimetype="image/png")
    return Response(status=400)
