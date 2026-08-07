(() => {
  "use strict";

  const root = document.documentElement;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const revealItems = [...document.querySelectorAll(".reveal,[data-stagger]")];
  document.querySelectorAll("[data-stagger]").forEach((group) => {
    [...group.children].forEach((child, index) => child.style.setProperty("--i", String(Math.min(index, 5))));
  });

  if (!reduceMotion && "IntersectionObserver" in window && revealItems.length) {
    root.classList.add("reveal-ready");
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("in");
        revealObserver.unobserve(entry.target);
      });
    }, { threshold: 0.05, rootMargin: "0px 0px 180px 0px" });

    revealItems.forEach((item) => revealObserver.observe(item));
    window.setTimeout(() => {
      revealItems.forEach((item) => item.classList.add("in"));
    }, 2200);
  } else {
    revealItems.forEach((item) => item.classList.add("in"));
  }

  const contact = document.getElementById("contact");
  const navLinks = [...document.querySelectorAll(".nav-links a[href^='#']")];
  const navSections = navLinks
    .map((link) => ({ link, section: document.querySelector(link.getAttribute("href")) }))
    .filter((item) => item.section);

  const setActiveNav = (activeLink = null) => {
    navLinks.forEach((link) => {
      const active = activeLink === link;
      link.classList.toggle("active", Boolean(active));
      if (active) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  };

  if ("IntersectionObserver" in window && navSections.length) {
    const navState = new Map();
    const navObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => navState.set(entry.target, entry.isIntersecting));
      if (contact && navState.get(contact)) {
        setActiveNav();
        return;
      }
      let current = null;
      navSections.forEach((item) => {
        if (navState.get(item.section)) current = item;
      });
      setActiveNav(current?.link || null);
    }, { threshold: 0, rootMargin: "-88px 0px -68% 0px" });
    navSections.forEach((item) => navObserver.observe(item.section));
    if (contact) navObserver.observe(contact);
  } else {
    setActiveNav();
  }

  const navSentinel = document.getElementById("navsentinel");
  if (navSentinel && "IntersectionObserver" in window) {
    new IntersectionObserver(([entry]) => {
      root.classList.toggle("scrolled", !entry.isIntersecting);
    }, { threshold: 0 }).observe(navSentinel);
  } else {
    root.classList.add("scrolled");
  }

  const rails = [...document.querySelectorAll("[data-rail]")];
  if (rails.length) {
    const syncRail = (node) => {
      const max = node.scrollWidth - node.clientWidth;
      const ratio = max > 4 ? node.scrollLeft / max : -1;
      node.dataset.edge = ratio < 0 ? "none" : ratio < 0.02 ? "start" : ratio > 0.98 ? "end" : "mid";
    };
    let railPending = false;
    const syncAllRails = () => {
      railPending = false;
      rails.forEach(syncRail);
    };
    const queueRails = () => {
      if (railPending) return;
      railPending = true;
      window.requestAnimationFrame(syncAllRails);
    };
    rails.forEach((node) => node.addEventListener("scroll", queueRails, { passive: true }));
    window.addEventListener("resize", queueRails, { passive: true });
    syncAllRails();
  }

  // iOS не применяет :active к элементам без обработчика касания
  document.addEventListener("touchstart", () => {}, { passive: true });

  const menuButton = document.querySelector(".nav-menu");
  const menu = document.getElementById("navmenu");
  if (menuButton && menu) {
    const setMenu = (open, focusFirst = false) => {
      menu.classList.toggle("open", open);
      menuButton.setAttribute("aria-expanded", String(open));
      menuButton.setAttribute("aria-label", open ? "Закрыть меню" : "Открыть меню");
      if (open && focusFirst) menu.querySelector("a")?.focus();
    };
    menuButton.addEventListener("click", () => {
      const open = !menu.classList.contains("open");
      setMenu(open, open);
    });
    menu.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => setMenu(false)));
    document.addEventListener("click", (event) => {
      if (menu.classList.contains("open") && !event.target.closest(".site-nav")) setMenu(false);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape" || !menu.classList.contains("open")) return;
      setMenu(false);
      menuButton.focus();
    });
    window.addEventListener("resize", () => {
      if (window.innerWidth > 768) setMenu(false);
    }, { passive: true });
  }

  let caseHook = null;
  let streamHook = null;

  const openHashTarget = (scrollToTarget = false) => {
    if (!window.location.hash || window.location.hash.length < 2) return;
    if (window.location.hash.startsWith("#stream-") && streamHook) {
      streamHook(window.location.hash.slice(8), scrollToTarget);
      return;
    }
    let target = null;
    try {
      target = document.querySelector(window.location.hash);
    } catch (_) {
      return;
    }
    if (!target) return;
    if (target.classList.contains("case-card") && caseHook) {
      caseHook(target, scrollToTarget);
      return;
    }
    let disclosure = target.matches("details")
      ? target
      : target.closest("details");
    while (disclosure) {
      disclosure.open = true;
      disclosure = disclosure.parentElement?.closest("details");
    }
    let revealParent = target;
    while (revealParent) {
      if (revealParent.classList?.contains("reveal")) revealParent.classList.add("in");
      revealParent = revealParent.parentElement;
    }
    target.querySelectorAll?.(".reveal").forEach((item) => item.classList.add("in"));
    if (scrollToTarget) {
      window.requestAnimationFrame(() => {
        target.scrollIntoView({ behavior: "instant", block: "start" });
      });
    }
  };
  window.addEventListener("hashchange", () => openHashTarget(true));
  window.addEventListener("load", () => {
    openHashTarget(true);
    window.setTimeout(() => openHashTarget(true), 320);
  }, { once: true });
  openHashTarget(false);

  const mobileCta = document.querySelector(".mobile-cta");
  const heroCta = document.querySelector("[data-placement='hero']");
  if (mobileCta && "IntersectionObserver" in window) {
    const blockers = [heroCta, contact, document.querySelector(".footer")].filter(Boolean);
    const blockerState = new Map(blockers.map((element) => {
      const box = element.getBoundingClientRect();
      return [element, box.bottom > 0 && box.top < window.innerHeight];
    }));
    const updateMobileCta = () => {
      mobileCta.classList.toggle("hide", [...blockerState.values()].some(Boolean));
    };
    const mobileCtaObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => blockerState.set(entry.target, entry.isIntersecting));
      updateMobileCta();
    }, { threshold: 0.12 });
    blockers.forEach((element) => mobileCtaObserver.observe(element));
    updateMobileCta();
  } else if (mobileCta) {
    mobileCta.classList.add("hide");
  }

  const tooltip = document.getElementById("tip");
  let tooltipOwner = null;
  let tooltipClickOwner = null;
  const positionTooltip = (owner) => {
    if (!tooltip || !owner) return;
    tooltip.textContent = owner.dataset.definition || "";
    tooltip.classList.add("show");
    tooltip.setAttribute("aria-hidden", "false");
    tooltip.style.left = "0px";
    tooltip.style.top = "0px";
    const ownerBox = owner.getBoundingClientRect();
    const tipWidth = tooltip.offsetWidth;
    const tipHeight = tooltip.offsetHeight;
    const left = Math.min(Math.max(8, ownerBox.left), window.innerWidth - tipWidth - 8);
    let top = ownerBox.top - tipHeight - 10;
    if (top < 8) top = ownerBox.bottom + 10;
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${Math.min(top, window.innerHeight - tipHeight - 8)}px`;
    tooltipOwner = owner;
  };
  const hideTooltip = () => {
    if (tooltip) {
      tooltip.classList.remove("show");
      tooltip.setAttribute("aria-hidden", "true");
    }
    tooltipOwner = null;
    tooltipClickOwner = null;
  };

  document.addEventListener("pointerover", (event) => {
    if (event.pointerType && event.pointerType !== "mouse") return;
    const owner = event.target.closest(".tooltip-term");
    if (owner) positionTooltip(owner);
    else if (tooltipOwner) hideTooltip();
  });
  document.addEventListener("focusin", (event) => {
    const owner = event.target.closest(".tooltip-term");
    if (owner) positionTooltip(owner);
    else hideTooltip();
  });
  document.addEventListener("click", (event) => {
    const owner = event.target.closest(".tooltip-term");
    if (!owner) {
      hideTooltip();
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    if (tooltipClickOwner === owner && tooltipOwner === owner && tooltip.classList.contains("show")) {
      hideTooltip();
      return;
    }
    positionTooltip(owner);
    tooltipClickOwner = owner;
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") hideTooltip();
  });
  window.addEventListener("wheel", hideTooltip, { passive: true });
  window.addEventListener("touchmove", hideTooltip, { passive: true });
  window.addEventListener("scrollend", hideTooltip, { passive: true });

  const track = (name, properties) => {
    try {
      const viewport = window.innerWidth <= 390 ? "mobile_narrow" : window.innerWidth <= 768 ? "mobile" : window.innerWidth <= 1024 ? "tablet" : "desktop";
      const eventProperties = { ...properties, viewport };
      if (typeof window.__track === "function") window.__track(name, eventProperties);
      window.dispatchEvent(new CustomEvent("portfolio:track", {
        detail: { name, properties: eventProperties }
      }));
    } catch (_) {
      // Аналитика является необязательным подключаемым слоем
    }
  };

  document.querySelectorAll("[data-event]").forEach((element) => {
    element.addEventListener("click", () => {
      track(element.dataset.event, {
        channel: element.dataset.channel || "",
        placement: element.dataset.placement || ""
      });
    });
  });

  const streamTabs = [...document.querySelectorAll(".stream-tab")];
  const streamPanels = new Map(
    [...document.querySelectorAll(".stream-panel")].map((panel) => [panel.id.replace("stream-", ""), panel])
  );

  const selectStream = (slug, { focusTab = false, silent = false } = {}) => {
    if (!streamPanels.has(slug)) return;
    streamTabs.forEach((tab) => {
      const active = tab.dataset.stream === slug;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
      if (active && focusTab) tab.focus();
      if (active) tab.scrollIntoView({ block: "nearest", inline: "nearest" });
    });
    streamPanels.forEach((panel, key) => {
      const active = key === slug;
      panel.hidden = !active;
      panel.classList.toggle("is-active", active);
    });
    if (!silent) track("stream_select", { stream: slug });
  };

  streamHook = (slug, doScroll) => {
    selectStream(slug, { silent: true });
    if (doScroll) document.getElementById("services")?.scrollIntoView({ behavior: "instant", block: "start" });
  };

  streamTabs.forEach((tab, index) => {
    tab.addEventListener("click", () => {
      root.classList.add("streams-armed");
      selectStream(tab.dataset.stream);
    });
    tab.addEventListener("keydown", (event) => {
      const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
      let next = null;
      if (step) next = streamTabs[(index + step + streamTabs.length) % streamTabs.length];
      else if (event.key === "Home") next = streamTabs[0];
      else if (event.key === "End") next = streamTabs[streamTabs.length - 1];
      if (!next) return;
      event.preventDefault();
      selectStream(next.dataset.stream, { focusTab: true });
    });
  });

  const streamTabList = document.querySelector(".stream-tabs");
  if (streamTabList) streamTabList.scrollLeft = 0;
  streamTabs.forEach((tab, index) => tab.style.setProperty("--i", String(index)));

  if (streamTabList && "IntersectionObserver" in window) {
    const streamsViewObserver = new IntersectionObserver((entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return;
      streamTabList.classList.add("is-cued");
      track("services_view", { streams: streamTabs.length, cases: document.querySelectorAll(".case-card").length });
      streamsViewObserver.disconnect();
    }, { threshold: 0.35 });
    streamsViewObserver.observe(streamTabList);
  } else if (streamTabList) {
    streamTabList.classList.add("is-cued");
  }

  const modal = document.getElementById("caseModal");
  const cases = [...document.querySelectorAll(".case-card")];

  if (modal && cases.length) {
    const inner = modal.querySelector(".case-modal-inner");
    const slots = {
      stream: modal.querySelector(".case-modal-stream"),
      kicker: modal.querySelector(".case-modal-kicker"),
      title: modal.querySelector(".case-modal-title"),
      context: modal.querySelector(".case-modal-context"),
      claims: modal.querySelector(".case-modal-claims"),
      facts: modal.querySelector(".case-modal-facts")
    };
    const prevButton = modal.querySelector("[data-case-nav='prev']");
    const nextButton = modal.querySelector("[data-case-nav='next']");
    let opener = null;
    let current = null;

    const streamOf = (card) => card.closest(".stream-panel")?.id.replace("stream-", "") || "";
    const siblings = (card) => [...(card.closest(".case-grid")?.querySelectorAll(".case-card") || [])];
    const labelOf = (slug) => document.querySelector(`.stream-tab[data-stream="${slug}"] .stream-tab-name`)?.textContent.trim() || "";

    const fill = (card) => {
      current = card;
      const slug = streamOf(card);
      slots.stream.textContent = labelOf(slug);
      slots.kicker.textContent = card.querySelector(".case-kicker")?.textContent.trim() || "";
      slots.title.textContent = card.querySelector(".case-title")?.textContent.trim() || "";
      slots.context.textContent = card.querySelector(".case-context")?.textContent.trim() || "";
      const claims = card.querySelector(".claim-stack");
      slots.claims.innerHTML = claims ? claims.innerHTML : "";
      slots.claims.hidden = !claims;
      const facts = card.querySelector(".project-facts");
      slots.facts.innerHTML = facts ? facts.innerHTML : "";
      const list = siblings(card);
      const index = list.indexOf(card);
      prevButton.disabled = index <= 0;
      nextButton.disabled = index < 0 || index >= list.length - 1;
      if (inner) inner.scrollTop = 0;
      try {
        history.replaceState(null, "", `#${card.id}`);
      } catch (_) {
        // Адресная строка не критична для работы окна
      }
    };

    const openCase = (card, scrollToStream = false) => {
      const slug = streamOf(card);
      if (slug) selectStream(slug, { silent: true });
      if (scrollToStream) {
        document.getElementById("services")?.scrollIntoView({ behavior: "instant", block: "start" });
      }
      if (!modal.open) {
        opener = document.activeElement;
        modal.showModal();
      }
      fill(card);
      track("case_open", { case: card.id, stream: slug });
      modal.querySelector(".case-modal-close")?.focus();
    };
    caseHook = openCase;

    cases.forEach((card) => {
      const summary = card.querySelector("summary");
      summary?.addEventListener("click", (event) => {
        event.preventDefault();
        openCase(card);
      });
    });

    const step = (delta) => {
      if (!current) return;
      const list = siblings(current);
      const next = list[list.indexOf(current) + delta];
      if (next) openCase(next);
    };
    prevButton?.addEventListener("click", () => step(-1));
    nextButton?.addEventListener("click", () => step(1));

    const share = modal.querySelector(".case-modal-share");
    const shareStatus = document.getElementById("shareStatus");
    if (share) {
      const shareLabel = share.textContent;
      const report = (message) => {
        share.textContent = message;
        if (shareStatus) shareStatus.textContent = message;
        window.setTimeout(() => {
          share.textContent = shareLabel;
          if (shareStatus) shareStatus.textContent = "";
        }, 1800);
      };
      share.addEventListener("click", () => {
        const url = window.location.href;
        const copying = navigator.clipboard?.writeText(url);
        if (copying) copying.then(() => report("Ссылка скопирована"), () => report("Скопируйте адрес из строки браузера"));
        else report("Скопируйте адрес из строки браузера");
      });
    }

    modal.querySelector(".case-modal-close")?.addEventListener("click", () => modal.close());
    modal.addEventListener("click", (event) => {
      if (event.target === modal) modal.close();
    });
    modal.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") step(-1);
      if (event.key === "ArrowRight") step(1);
    });
    modal.addEventListener("close", () => {
      try {
        history.replaceState(null, "", window.location.pathname + window.location.search);
      } catch (_) {
        // Адресная строка не критична для работы окна
      }
      if (opener && document.contains(opener)) opener.focus();
      opener = null;
      current = null;
    });
  }

  document.querySelectorAll(".faq details").forEach((item, index) => {
    item.addEventListener("toggle", () => {
      if (item.open) track("faq_open", { item: index + 1 });
    });
  });
})();
