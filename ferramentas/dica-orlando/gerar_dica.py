#!/usr/bin/env python3
"""Gera o vídeo vertical "Dica de Orlando do dia" (Ronatrip).

Uso: python3 gerar_dica.py dados.json saida/

dados.json:
{
  "numero": 1,
  "tema": "COMPRAS",
  "fundo": "fundo.png",               # imagem 9:16 (gerada sem texto/logo)
  "narracao": "narracao.mp3",
  "logo": "logo-ronatrip.png",        # versão escura (fundo claro)
  "cortes": [0, 5.2, 10.75, 13.45],   # início de cada quadro, em segundos
  "quadros": [
    {"tipo": "titulo", "titulo": "...", "sub": "..."},
    {"tipo": "numero", "numero": "+6,5%", "linha": "...", "extra": "...", "fonte": "..."},
    {"tipo": "titulo", "titulo": "...", "sub": "..."},
    {"tipo": "final"}
  ],
  "whatsapp": "+1 (407) 409-6253"
}
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
IVORY = (247, 242, 232)
INK = (51, 48, 44)
OLIVE = (150, 143, 104)
FONT_DIR = os.environ.get("DICA_FONTES") or (os.path.join(os.path.dirname(os.path.abspath(__file__)), "fontes"))


def font(weight, size):
    nomes = {"r": "Inter-Regular.otf", "m": "Inter-Medium.otf", "sb": "Inter-SemiBold.otf",
             "b": "Inter-Bold.otf", "xb": "InterDisplay-ExtraBold.otf", "dsb": "InterDisplay-SemiBold.otf"}
    p = os.path.join(FONT_DIR, nomes[weight])
    if not os.path.exists(p):
        p = os.path.join(FONT_DIR, "Inter-Bold.otf")
    return ImageFont.truetype(p, size)


def quebra(draw, texto, f, largura):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if draw.textlength(teste, font=f) <= largura:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def fundo_cover(caminho):
    im = Image.open(caminho).convert("RGB")
    esc = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * esc), round(im.height * esc)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def cabecalho(img, d, num, tema):
    # etiqueta superior
    rot = f"DICA DE ORLANDO · Nº {num}"
    f = font("sb", 30)
    tw = d.textlength(rot, font=f)
    x0, y0 = 70, 110
    d.rounded_rectangle((x0, y0, x0 + tw + 56, y0 + 62), radius=31, fill=IVORY + (235,))
    d.text((x0 + 28, y0 + 14), rot, font=f, fill=INK)
    selo = "Imagem e voz geradas por IA"
    fs = font("m", 24)
    sw = d.textlength(selo, font=fs)
    d.rounded_rectangle((W - 70 - sw - 36, y0 + 8, W - 70, y0 + 54), radius=23, fill=(0, 0, 0, 110))
    d.text((W - 70 - sw - 18, y0 + 17), selo, font=fs, fill=(255, 255, 255))


def cartao(d, y, altura):
    d.rounded_rectangle((60, y, W - 60, y + altura), radius=36, fill=IVORY + (238,))


def quadro_titulo(base, q, num, tema):
    img = base.copy().convert("RGBA")
    camada = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    cabecalho(img, d, num, tema)
    ft, fsub, ftema = font("xb", 76), font("r", 40), font("sb", 30)
    lt = quebra(d, q["titulo"], ft, W - 220)
    ls = quebra(d, q.get("sub", ""), fsub, W - 220) if q.get("sub") else []
    alt = 70 + 50 + len(lt) * 92 + (30 + len(ls) * 54 if ls else 0) + 70
    y = 300
    cartao(d, y, alt)
    yy = y + 70
    d.text((110, yy), tema, font=ftema, fill=OLIVE)
    yy += 50
    for l in lt:
        d.text((110, yy), l, font=ft, fill=INK)
        yy += 92
    if ls:
        yy += 30
        for l in ls:
            d.text((110, yy), l, font=fsub, fill=INK)
            yy += 54
    img.alpha_composite(camada)
    return img.convert("RGB")


def quadro_numero(base, q, num, tema):
    img = base.copy().convert("RGBA")
    camada = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    cabecalho(img, d, num, tema)
    fn, fl, fe, ff = font("xb", 190), font("sb", 46), font("r", 42), font("r", 26)
    ll = quebra(d, q["linha"], fl, W - 220)
    le = quebra(d, q.get("extra", ""), fe, W - 220) if q.get("extra") else []
    alt = 60 + 200 + 20 + len(ll) * 60 + (40 + len(le) * 56 if le else 0) + (60 if q.get("fonte") else 0) + 60
    y = 300
    cartao(d, y, alt)
    yy = y + 50
    d.text((100, yy), q["numero"], font=fn, fill=INK)
    yy += 220
    for l in ll:
        d.text((110, yy), l, font=fl, fill=INK)
        yy += 60
    if le:
        yy += 40
        d.line((110, yy - 20, 330, yy - 20), fill=OLIVE, width=4)
        for l in le:
            d.text((110, yy), l, font=fe, fill=INK)
            yy += 56
    if q.get("fonte"):
        yy += 24
        d.text((110, yy), q["fonte"], font=ff, fill=OLIVE)
    img.alpha_composite(camada)
    return img.convert("RGB")


def quadro_final(base, dados):
    fundo = base.copy().filter(ImageFilter.GaussianBlur(18)).convert("RGBA")
    fundo.alpha_composite(Image.new("RGBA", (W, H), IVORY + (215,)))
    d = ImageDraw.Draw(fundo)
    logo = Image.open(dados["logo"]).convert("RGBA")
    lw = 820
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    y = 560
    fundo.alpha_composite(logo, ((W - lw) // 2, y))
    yy = y + logo.height + 110
    for texto, f, cor in [("Dica de Orlando todo dia", font("dsb", 56), INK),
                          ("Atendimento em português", font("r", 40), INK),
                          ("WhatsApp " + dados["whatsapp"], font("sb", 44), OLIVE)]:
        tw = d.textlength(texto, font=f)
        d.text(((W - tw) / 2, yy), texto, font=f, fill=cor)
        yy += 86
    selo = "Imagem e voz geradas por IA"
    fs = font("m", 24)
    sw = d.textlength(selo, font=fs)
    d.text(((W - sw) / 2, 1420), selo, font=fs, fill=OLIVE)
    return fundo.convert("RGB")


def main(dados_path, saida):
    os.makedirs(saida, exist_ok=True)
    base_dir = os.path.dirname(os.path.abspath(dados_path))
    with open(dados_path, encoding="utf-8") as fh:
        dados = json.load(fh)
    for k in ("fundo", "narracao", "logo"):
        if not os.path.isabs(dados[k]):
            dados[k] = os.path.join(base_dir, dados[k])
    base = fundo_cover(dados["fundo"])
    num, tema = dados["numero"], dados["tema"]
    imgs = []
    for i, q in enumerate(dados["quadros"]):
        if q["tipo"] == "titulo":
            im = quadro_titulo(base, q, num, tema)
        elif q["tipo"] == "numero":
            im = quadro_numero(base, q, num, tema)
        else:
            im = quadro_final(base, dados)
        p = os.path.join(saida, f"q{i+1}.jpg")
        im.save(p, quality=93)
        imgs.append(p)

    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", dados["narracao"]]).strip())
    total = dur + 0.8
    cortes = dados["cortes"] + [total]
    tempos = [cortes[i + 1] - cortes[i] for i in range(len(imgs))]
    fade = 0.35
    args = ["ffmpeg", "-y"]
    for p, t in zip(imgs, tempos):
        args += ["-loop", "1", "-t", f"{t + fade:.3f}", "-i", p]
    args += ["-i", dados["narracao"]]
    filtros = []
    for i, t in enumerate(tempos):
        frames = int((t + fade) * 30)
        filtros.append(f"[{i}:v]scale=1188:2112,zoompan=z='min(1+0.0006*on,1.08)':d={frames}:"
                       f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps=30,setsar=1[v{i}]")
    ultimo, off = "v0", 0.0
    for i in range(1, len(tempos)):
        off += tempos[i - 1]
        filtros.append(f"[{ultimo}][v{i}]xfade=transition=fade:duration={fade}:offset={off - fade/2:.3f}[x{i}]")
        ultimo = f"x{i}"
    a = len(imgs)
    filtros.append(f"[{a}:a]apad=pad_dur=1,atrim=0:{total:.3f}[a]")
    args += ["-filter_complex", ";".join(filtros), "-map", f"[{ultimo}]", "-map", "[a]",
             "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
             os.path.join(saida, "dica.mp4")]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # folha de conferência
    th = [Image.open(p).resize((270, 480)) for p in imgs]
    folha = Image.new("RGB", (270 * len(th) + 10 * (len(th) - 1), 480), "white")
    for i, t in enumerate(th):
        folha.paste(t, (i * 280, 0))
    folha.save(os.path.join(saida, "quadros.jpg"), quality=88)
    print("ok", round(total, 2), "s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
