/* Aula interativa: partitura (abcjs), som sintetizado no navegador (piano ou violão),
   teclado clicável e exercícios com correção imediata. Sem dependências além do abcjs. */
(function () {
  "use strict";

  var dados = JSON.parse(document.getElementById("dados-aula").textContent);

  function guardar(chave, valor) { try { localStorage.setItem(chave, valor); } catch (e) { /* sem armazenamento */ } }
  function ler(chave) { try { return localStorage.getItem(chave); } catch (e) { return null; } }

  var estado = {
    timbre: ler("music-tutor:timbre") || dados.preferencias.timbre || "piano",
    fatorAndamento: 1
  };

  /* ------------------------------------------------------------ Som */
  var Som = (function () {
    var ctx = null, saidas = {}, cache = new Map(), ativos = new Set();

    function contexto() {
      if (!ctx) {
        var AC = window.AudioContext || window.webkitAudioContext;
        ctx = new AC();
        var comp = ctx.createDynamicsCompressor();
        comp.threshold.value = -14; comp.ratio.value = 3;
        var mestre = ctx.createGain(); mestre.gain.value = 0.9;
        mestre.connect(comp); comp.connect(ctx.destination);

        var piano = ctx.createBiquadFilter(); piano.type = "lowpass"; piano.frequency.value = 9000;
        piano.connect(mestre);

        var corpo1 = ctx.createBiquadFilter(); corpo1.type = "peaking"; corpo1.frequency.value = 105; corpo1.Q.value = 1.4; corpo1.gain.value = 4;
        var corpo2 = ctx.createBiquadFilter(); corpo2.type = "peaking"; corpo2.frequency.value = 230; corpo2.Q.value = 1.2; corpo2.gain.value = 2.5;
        var brilho = ctx.createBiquadFilter(); brilho.type = "lowpass"; brilho.frequency.value = 4200;
        corpo1.connect(corpo2); corpo2.connect(brilho); brilho.connect(mestre);
        saidas = { piano: piano, violao: corpo1 };
      }
      if (ctx.state === "suspended") ctx.resume();
      return ctx;
    }

    function freq(m) { return 440 * Math.pow(2, (m - 69) / 12); }

    function normalizar(dados, alvo) {
      var pico = 0;
      for (var i = 0; i < dados.length; i++) { var a = Math.abs(dados[i]); if (a > pico) pico = a; }
      if (pico > 0) { var k = alvo / pico; for (var j = 0; j < dados.length; j++) dados[j] *= k; }
    }

    // Piano: soma de parciais levemente inarmônicos, duas cordas desafinadas e batida do martelo.
    function bufferPiano(m) {
      var sr = ctx.sampleRate, f0 = freq(m);
      var dur = Math.max(1.6, Math.min(4.5, 4.5 - (m - 48) * 0.06));
      var n = Math.floor(sr * dur), dados = new Float32Array(n);
      var B = 0.00012 * Math.pow(2, (m - 48) / 18);
      var limite = Math.min(7000, sr / 2 - 500);
      for (var h = 1; h <= 40; h++) {
        var fh = h * f0 * Math.sqrt(1 + B * h * h);
        if (fh > limite) break;
        var amp = Math.pow(h, -1.15) * Math.abs(Math.sin(Math.PI * h * 0.12)) * (1 + 0.6 / h);
        var d1 = (0.55 + 0.32 * h) * Math.pow(f0 / 261.6, 0.55);
        var d2 = d1 * 0.16;
        [0.9996, 1.0004].forEach(function (desv) {
          var w = 2 * Math.PI * fh * desv / sr;
          var c = Math.cos(w), s = Math.sin(w);
          var fase = Math.random() * 2 * Math.PI;
          var re = Math.cos(fase), im = Math.sin(fase);
          var e1 = Math.exp(-d1 / sr), e2 = Math.exp(-d2 / sr), a1 = 0.72 * amp * 0.5, a2 = 0.28 * amp * 0.5;
          for (var i = 0; i < n; i++) {
            dados[i] += (a1 + a2) * im;
            var nre = re * c - im * s; im = re * s + im * c; re = nre;
            a1 *= e1; a2 *= e2;
          }
        });
      }
      var ataque = Math.floor(sr * 0.002), martelo = Math.floor(sr * 0.018), lp = 0;
      for (var i = 0; i < n; i++) {
        if (i < martelo) { lp += 0.25 * ((Math.random() * 2 - 1) - lp); dados[i] += lp * 0.05 * (1 - i / martelo); }
        if (i < ataque) dados[i] *= i / ataque;
      }
      normalizar(dados, 0.42);
      return dados;
    }

    // Violão: Karplus-Strong com atraso fracionário para manter a afinação nas notas agudas.
    function bufferViolao(m) {
      var sr = ctx.sampleRate, f0 = freq(m);
      var dur = Math.max(1.4, Math.min(3.8, 3.8 - (m - 40) * 0.05));
      var n = Math.floor(sr * dur), y = new Float32Array(n);
      var P = sr / f0 - 0.5;
      var L = Math.ceil(P) + 2, lp = 0;
      for (var i = 0; i < L; i++) { lp += 0.55 * ((Math.random() * 2 - 1) - lp); y[i] = lp; }
      var pos = Math.max(1, Math.round(P * 0.18));
      for (var k = L - 1; k >= pos; k--) y[k] -= 0.6 * y[k - pos];
      var t60 = Math.max(0.9, 3.2 - (m - 40) * 0.05);
      var g = Math.pow(10, -3 / (t60 * f0));
      for (var t = L; t < n; t++) {
        var d = t - P, i0 = Math.floor(d), fr = d - i0;
        var a = y[i0] * (1 - fr) + y[i0 + 1] * fr;
        var b = y[i0 - 1] * (1 - fr) + y[i0] * fr;
        y[t] = g * 0.5 * (a + b);
      }
      var ataque = Math.floor(sr * 0.003);
      for (var j = 0; j < ataque; j++) y[j] *= j / ataque;
      normalizar(y, 0.5);
      return y;
    }

    function buffer(m, timbre) {
      var chave = timbre + ":" + m;
      if (!cache.has(chave)) {
        var dadosSom = timbre === "violao" ? bufferViolao(m) : bufferPiano(m);
        var b = ctx.createBuffer(1, dadosSom.length, ctx.sampleRate);
        b.copyToChannel(dadosSom, 0);
        cache.set(chave, b);
      }
      return cache.get(chave);
    }

    function nota(m, quando, duracao, timbre, intensidade) {
      var fonte = ctx.createBufferSource();
      fonte.buffer = buffer(m, timbre);
      var ganho = ctx.createGain();
      ganho.gain.setValueAtTime(intensidade, quando);
      var fim = quando + duracao;
      if (timbre === "violao") ganho.gain.setTargetAtTime(0, fim + 0.1, 0.22);
      else ganho.gain.setTargetAtTime(0, fim, 0.09);
      fonte.connect(ganho); ganho.connect(saidas[timbre]);
      fonte.start(quando);
      fonte.stop(Math.min(quando + fonte.buffer.duration, fim + 1.5));
      var registro = { fonte: fonte, ganho: ganho };
      ativos.add(registro);
      fonte.onended = function () { ativos.delete(registro); };
    }

    function parar() {
      if (!ctx) return;
      ativos.forEach(function (r) {
        try { r.ganho.gain.cancelScheduledValues(ctx.currentTime); r.ganho.gain.setTargetAtTime(0, ctx.currentTime, 0.03); r.fonte.stop(ctx.currentTime + 0.2); } catch (e) { /* já parou */ }
      });
      ativos.clear();
    }

    // eventos: [{midis: [..], duracao: tempos}]
    function tocarEventos(eventos, andamento, aoPasso, aoFim) {
      var c = contexto();
      var timbre = estado.timbre;
      eventos.forEach(function (ev) { ev.midis.forEach(function (m) { buffer(m, timbre); }); });
      var spb = 60 / (andamento * estado.fatorAndamento);
      var inicio = c.currentTime + 0.08, t = inicio, timers = [];
      eventos.forEach(function (ev, idx) {
        var dur = ev.duracao * spb;
        ev.midis.forEach(function (m) { nota(m, t, dur * 0.95, timbre, ev.midis.length > 1 ? 0.62 : 0.8); });
        var atraso = (t - c.currentTime) * 1000;
        timers.push(setTimeout(function () { if (aoPasso) aoPasso(idx); }, Math.max(0, atraso)));
        t += dur;
      });
      timers.push(setTimeout(function () { if (aoFim) aoFim(); }, (t - c.currentTime) * 1000 + 250));
      return { cancelar: function () { timers.forEach(clearTimeout); parar(); if (aoFim) aoFim(); } };
    }

    return { contexto: contexto, tocarEventos: tocarEventos, parar: parar };
  })();

  /* ------------------------------------------------------------ Partituras */
  var elementosPorExemplo = {};
  var abcjsPronto = typeof window.ABCJS !== "undefined";

  function desenharPartituras() {
    document.querySelectorAll("[data-partitura]").forEach(function (alvo) {
      var id = alvo.getAttribute("data-partitura");
      var ex = dados.exemplos[id];
      if (!ex) return;
      if (!abcjsPronto) {
        alvo.textContent = "A partitura não carregou (sem conexão). O áudio continua funcionando.";
        alvo.classList.add("sem-partitura");
        return;
      }
      ABCJS.renderAbc(alvo, ex.abc, {
        responsive: "resize",
        add_classes: true,
        paddingtop: 6,
        paddingbottom: 6,
        paddingleft: 0,
        paddingright: 0,
        foregroundColor: "currentColor",
        staffwidth: 520
      });
      elementosPorExemplo[id] = elementosPorExemplo[id] || [];
      elementosPorExemplo[id].push(alvo);
    });
  }

  function marcarNota(id, idx) {
    (elementosPorExemplo[id] || []).forEach(function (alvo) {
      var notas = alvo.querySelectorAll(".abcjs-note, .abcjs-rest");
      notas.forEach(function (el, i) { el.classList.toggle("tocando", i === idx); });
    });
  }

  /* ------------------------------------------------------------ Botões de tocar */
  var tocandoAgora = null;

  function aviso(texto) {
    var el = document.createElement("div");
    el.className = "aviso-som";
    el.setAttribute("role", "status");
    el.textContent = texto;
    document.body.appendChild(el);
    setTimeout(function () { el.remove(); }, 3500);
  }

  function tocarComBotao(botao, eventos, andamento, aoPasso) {
    if (tocandoAgora && tocandoAgora.botao === botao) { tocandoAgora.controle.cancelar(); return; }
    if (tocandoAgora) tocandoAgora.controle.cancelar();
    var texto = botao.querySelector(".texto"), original = texto ? texto.textContent : "";
    botao.classList.add("ativo");
    if (texto) texto.textContent = "Parar";
    var registro = { botao: botao };
    try {
      registro.controle = Som.tocarEventos(eventos, andamento, aoPasso, function () {
        botao.classList.remove("ativo");
        if (texto) texto.textContent = original;
        if (aoPasso) aoPasso(-1);
        if (tocandoAgora === registro) tocandoAgora = null;
      });
      tocandoAgora = registro;
    } catch (e) {
      botao.classList.remove("ativo");
      if (texto) texto.textContent = original;
      aviso("Este navegador não liberou o áudio. Toque de novo ou verifique o volume.");
    }
  }

  document.addEventListener("click", function (evento) {
    var botao = evento.target.closest("[data-tocar]");
    if (botao) {
      var id = botao.getAttribute("data-tocar");
      var ex = dados.exemplos[id];
      tocarComBotao(botao, ex.eventos, ex.andamento, function (idx) { marcarNota(id, idx); });
      return;
    }
    var botaoTeclado = evento.target.closest("[data-tocar-teclado]");
    if (botaoTeclado) {
      var t = teclados[botaoTeclado.getAttribute("data-tocar-teclado")];
      var midis = t.dados.destaque.map(function (d) { return d.midi; }).sort(function (a, b) { return a - b; });
      var eventos = midis.map(function (m) { return { midis: [m], duracao: 1 }; });
      if (midis.length > 1) eventos.push({ midis: midis, duracao: 2 });
      tocarComBotao(botaoTeclado, eventos, 80, function (idx) {
        t.marcarSoando(idx < 0 ? [] : eventos[idx].midis);
      });
    }
  });

  /* ------------------------------------------------------------ Teclado */
  var BRANCAS = { 0: "Dó", 2: "Ré", 4: "Mi", 5: "Fá", 7: "Sol", 9: "Lá", 11: "Si" };
  var teclados = {};

  function criarTeclado(el, info, aoClicar) {
    var larguraBranca = 34, larguraPreta = 22, x = 0, teclas = {};
    for (var m = info.de; m <= info.ate; m++) {
      var classe = m % 12, branca = classe in BRANCAS;
      var b = document.createElement("button");
      b.type = "button";
      b.className = "tecla " + (branca ? "branca" : "preta");
      b.dataset.midi = m;
      var rotulo = document.createElement("span");
      rotulo.className = "nome";
      if (branca) {
        b.style.left = x + "px";
        b.style.width = larguraBranca + "px";
        if (classe === 0) rotulo.textContent = "Dó" + (Math.floor(m / 12) - 1);
        x += larguraBranca;
      } else {
        b.style.left = (x - larguraPreta / 2) + "px";
        b.style.width = larguraPreta + "px";
      }
      b.setAttribute("aria-label", branca ? BRANCAS[classe] + (Math.floor(m / 12) - 1) : "tecla preta");
      b.appendChild(rotulo);
      el.appendChild(b);
      teclas[m] = b;
    }
    el.style.width = x + "px";
    info.destaque.forEach(function (d) {
      var tecla = teclas[d.midi];
      if (!tecla) return;
      tecla.classList.add("destaque");
      tecla.querySelector(".nome").textContent = d.nome;
      tecla.setAttribute("aria-label", d.nome + " (destacada)");
    });
    el.addEventListener("click", function (evento) {
      var tecla = evento.target.closest(".tecla");
      if (!tecla) return;
      var midiTecla = Number(tecla.dataset.midi);
      if (aoClicar && aoClicar(midiTecla, tecla) === false) return;
      Som.tocarEventos([{ midis: [midiTecla], duracao: 1 }], 90);
      tecla.classList.add("soando");
      setTimeout(function () { tecla.classList.remove("soando"); }, 350);
    });
    return {
      dados: info,
      teclas: teclas,
      marcarSoando: function (midis) {
        Object.keys(teclas).forEach(function (k) { teclas[k].classList.toggle("soando", midis.indexOf(Number(k)) >= 0); });
      }
    };
  }

  /* ------------------------------------------------------------ Exercícios */
  var placar = { respondidos: 0, acertos: 0, total: dados.exercicios.length };

  function atualizarPlacar() {
    var el = document.getElementById("placar");
    if (!el) return;
    el.textContent = placar.respondidos === 0
      ? "Responda para ver seus acertos."
      : "Acertos: " + placar.acertos + " de " + placar.respondidos + " respondidos (" + placar.total + " no total).";
  }

  function mostrarRetorno(artigo, certo, texto) {
    var retorno = artigo.querySelector(".retorno");
    var veredito = retorno.querySelector(".veredito");
    veredito.textContent = texto;
    veredito.className = "veredito " + (certo ? "certo" : "errado");
    retorno.hidden = false;
    var oculto = artigo.querySelector(".exemplo.oculto");
    if (oculto) { oculto.hidden = false; }
    placar.respondidos += 1;
    if (certo) placar.acertos += 1;
    atualizarPlacar();
  }

  function prepararOpcoes(artigo, exe) {
    artigo.querySelectorAll(".opcao").forEach(function (botao) {
      botao.addEventListener("click", function () {
        var escolhida = Number(botao.dataset.opcao), certo = escolhida === exe.correta;
        artigo.querySelectorAll(".opcao").forEach(function (b) {
          b.disabled = true;
          if (Number(b.dataset.opcao) === exe.correta) b.classList.add("certa");
        });
        if (!certo) botao.classList.add("errada");
        mostrarRetorno(artigo, certo, certo ? "Isso mesmo." : "Ainda não. A resposta certa está marcada em verde.");
      });
    });
  }

  function prepararTecladoExercicio(artigo, exe) {
    var el = artigo.querySelector("[data-teclado-exercicio]");
    var respondido = false;
    var teclado = criarTeclado(el, exe.teclado, function (midiTecla, tecla) {
      if (respondido || midiTecla === exe.base) return true;
      respondido = true;
      var certo = midiTecla === exe.alvo;
      tecla.classList.add(certo ? "acertou" : "errou");
      if (certo) tecla.querySelector(".nome").textContent = exe.alvo_nome;
      if (!certo) {
        var alvo = teclado.teclas[exe.alvo];
        if (alvo) { alvo.classList.add("acertou"); alvo.querySelector(".nome").textContent = exe.alvo_nome; }
      }
      Som.tocarEventos([{ midis: [exe.base], duracao: 1 }, { midis: [midiTecla], duracao: 1 }, { midis: [exe.base, midiTecla], duracao: 2 }], 90);
      mostrarRetorno(artigo, certo, certo
        ? "Isso mesmo: " + exe.alvo_nome + " forma uma " + exe.intervalo_nome + "."
        : "Ainda não. A nota certa é " + exe.alvo_nome + ", marcada em verde.");
      return false;
    });
    var base = teclado.teclas[exe.base];
    if (base) { base.classList.add("base"); }
    artigo.querySelector("[data-tocar-base]").addEventListener("click", function () {
      Som.tocarEventos([{ midis: [exe.base], duracao: 1.5 }], 80);
    });
  }

  /* ------------------------------------------------------------ Controles */
  function aplicarTimbre(timbre) {
    estado.timbre = timbre;
    guardar("music-tutor:timbre", timbre);
    document.querySelectorAll("[data-timbre]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.timbre === timbre));
    });
  }

  document.querySelectorAll("[data-timbre]").forEach(function (b) {
    b.addEventListener("click", function () {
      aplicarTimbre(b.dataset.timbre);
      Som.tocarEventos([{ midis: [60, 64, 67], duracao: 1.5 }], 80);
    });
  });

  var andamento = document.getElementById("andamento");
  if (andamento) {
    andamento.addEventListener("input", function () {
      estado.fatorAndamento = Number(andamento.value) / 100;
      document.getElementById("andamento-valor").textContent = andamento.value + "%";
    });
  }

  var copiar = document.getElementById("copiar-pergunta");
  if (copiar) {
    copiar.addEventListener("click", function () {
      var texto = document.getElementById("pergunta-chat").textContent;
      function selecionar() {
        var r = document.createRange(); r.selectNodeContents(document.getElementById("pergunta-chat"));
        var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
        copiar.textContent = "Texto selecionado";
      }
      try {
        navigator.clipboard.writeText(texto).then(function () { copiar.textContent = "Copiada"; }, selecionar);
      } catch (e) { selecionar(); }
    });
  }

  /* ------------------------------------------------------------ Início */
  aplicarTimbre(estado.timbre);
  desenharPartituras();
  document.querySelectorAll("[data-teclado]").forEach(function (el) {
    var id = el.getAttribute("data-teclado");
    teclados[id] = criarTeclado(el, dados.teclados[id]);
  });
  dados.exercicios.forEach(function (exe) {
    var artigo = document.querySelector('[data-exercicio="' + exe.indice + '"]');
    if (!artigo) return;
    if (exe.tipo === "teclado") prepararTecladoExercicio(artigo, exe);
    else prepararOpcoes(artigo, exe);
  });
  atualizarPlacar();
})();
