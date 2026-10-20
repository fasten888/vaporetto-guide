(function () {
  "use strict";

  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });

    nav.addEventListener("click", function (event) {
      if (event.target.closest("a") && nav.classList.contains("open")) {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("open")) {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 920 && nav.classList.contains("open")) {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Optional browser speech for the pronunciation page (no audio files, no network).
  var speak = document.querySelector(".speak");
  if (speak) {
    if ("speechSynthesis" in window) {
      speak.addEventListener("click", function () {
        window.speechSynthesis.cancel();
        var utterance = new SpeechSynthesisUtterance(speak.getAttribute("data-say") || "vaporetto");
        utterance.lang = speak.getAttribute("data-lang") || "it-IT";
        utterance.rate = 0.82;
        window.speechSynthesis.speak(utterance);
      });
    } else {
      speak.hidden = true;
    }
  }

  // Open a FAQ when it is the target of an in-page link.
  if (location.hash) {
    try {
      var target = document.querySelector(location.hash);
      if (target && target.tagName === "DETAILS") target.open = true;
    } catch (error) {
      /* ignore malformed hashes */
    }
  }
})();
