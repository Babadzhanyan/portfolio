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

  const english = document.documentElement.lang.startsWith("en");

  const menuButton = document.querySelector(".nav-menu");
  const menu = document.getElementById("navmenu");
  if (menuButton && menu) {
    const setMenu = (open, focusFirst = false) => {
      menu.classList.toggle("open", open);
      menuButton.setAttribute("aria-expanded", String(open));
      menuButton.setAttribute("aria-label", english ? (open ? "Close menu" : "Open menu") : (open ? "Закрыть меню" : "Открыть меню"));
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
      if (getComputedStyle(menuButton).display === "none") setMenu(false);
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
    if (target.dataset.caseTarget) {
      target = document.getElementById(target.dataset.caseTarget) || target;
      if (target.classList.contains("case-card")) history.replaceState(null, "", `#${target.id}`);
    }
    if (target.classList.contains("company-anchor")) {
      streamHook?.(null, false);
      document.getElementById("services")?.scrollIntoView({ behavior: "instant", block: "start" });
      return;
    }
    if (target.id === "services") streamHook?.(null, false);
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

  const mobileCta = document.querySelector(".mobile-cta");
  const heroCta = document.querySelector("[data-placement='hero']");
  if (mobileCta && "IntersectionObserver" in window) {
    const blockers = [heroCta, contact, document.querySelector(".footer"), document.querySelector(".stream-tabs"), document.getElementById("industries")].filter(Boolean);
    const blockerState = new Map(blockers.map((element) => {
      const box = element.getBoundingClientRect();
      return [element, box.bottom > 0 && box.top < window.innerHeight];
    }));
    const updateMobileCta = () => {
      mobileCta.classList.toggle("hide", window.innerHeight < 520 || [...blockerState.values()].some(Boolean));
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
    tooltipOwner = owner;
    requestAnimationFrame(() => place(owner));
  };
  const place = (owner) => {
    if (!tooltip || tooltipOwner !== owner) return;
    const ownerBox = owner.getBoundingClientRect();
    const tipWidth = tooltip.offsetWidth;
    const tipHeight = tooltip.offsetHeight;
    const left = Math.min(Math.max(8, ownerBox.left), window.innerWidth - tipWidth - 8);
    const below = owner.dataset.tipPlacement === "below";
    let top = below ? ownerBox.bottom + 10 : ownerBox.top - tipHeight - 10;
    if (top < 8) top = ownerBox.bottom + 10;
    if (top + tipHeight > window.innerHeight - 8) top = Math.max(8, ownerBox.top - tipHeight - 10);
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${Math.min(top, window.innerHeight - tipHeight - 8)}px`;
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
    if (event.target.closest && event.target.closest("#tip")) return;
    if (event.pointerType && event.pointerType !== "mouse") return;
    const owner = event.target.closest(".tooltip-term");
    if (owner) positionTooltip(owner);
    else if (tooltipOwner) hideTooltip();
  });
  document.addEventListener("focusin", (event) => {
    if (event.target.closest && event.target.closest("#tip")) return;
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
  window.addEventListener("scrollend", () => {
    if (tooltipOwner === document.activeElement) { place(tooltipOwner); return; }
    hideTooltip();
  }, { passive: true });

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

  const cases = [...document.querySelectorAll(".case-card")];
  const careerPage = document.body.classList.contains("career");
  const controls = document.querySelector(".catalogue-controls");
  const industryPanel = document.getElementById("industries");
  const industryToggle = document.querySelector(".industry-mobile-toggle");
  const mobileFilters = matchMedia("(max-width: 900px)");
  const closeIndustries = () => industryToggle?.setAttribute("aria-expanded", "false");
  const placeIndustries = () => {
    if (!controls || !industryPanel) return;
    (mobileFilters.matches ? controls : document.querySelector(".catalogue-layout")).append(industryPanel);
    closeIndustries();
  };
  placeIndustries();
  mobileFilters.addEventListener("change", placeIndustries);
  industryToggle?.addEventListener("click", () => {
    industryToggle.setAttribute("aria-expanded", String(industryToggle.getAttribute("aria-expanded") !== "true"));
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && industryToggle?.getAttribute("aria-expanded") === "true") {
      closeIndustries();
      industryToggle.focus();
    }
  });
  document.addEventListener("click", event => {
    if (mobileFilters.matches && !controls?.contains(event.target)) closeIndustries();
  });
  const topNavigation = document.querySelector(".site-nav");
  if (topNavigation) new ResizeObserver(([entry]) => {
    document.documentElement.style.setProperty("--nav-height", `${entry.target.getBoundingClientRect().height}px`);
  }).observe(topNavigation);
  const streamTabs = [...document.querySelectorAll(".stream-tab")];
  const industryInputs = [...document.querySelectorAll("input[data-industry]")];
  const catalogue = document.getElementById("services");
  const results = document.getElementById("catalogueResults");
  const count = document.getElementById("catalogueCount");
  const empty = document.getElementById("catalogueEmpty");
  const selectedAreas = new Set();
  const selectedIndustries = new Set();
  const tags = (card, key) => (card.dataset[key] || "").split(" ").filter(Boolean);
  const intersects = (selection, values) => !selection.size || values.some(value => selection.has(value));
  const visibleCases = () => cases.filter(card => !card.hidden);

  const writeFilters = (mode, preserveHash = false) => {
    const url = new URL(location.href);
    url.searchParams.delete("company");
    for (const [key, values] of [["areas", [...selectedAreas]], ["industries", [...selectedIndustries]]]) {
      if (values.length) url.searchParams.set(key, values.join(","));
      else url.searchParams.delete(key);
    }
    if (!preserveHash) url.hash = "services";
    if (url.href !== location.href) history[mode + "State"](null, "", url);
  };

  const applyFilters = (mode = null, preserveHash = false) => {
    const chosen = selectedAreas.size > 0 || selectedIndustries.size > 0;
    catalogue?.classList.toggle("has-selection", chosen);
    if (results) results.hidden = !chosen;
    cases.forEach(card => {
      card.hidden = !careerPage && (!chosen || !intersects(selectedAreas, tags(card, "categories")) || !intersects(selectedIndustries, tags(card, "industries")));
      if (!careerPage) card.parentElement.hidden = card.hidden;
    });
    streamTabs.forEach(tab => {
      tab.setAttribute("aria-pressed", String(selectedAreas.has(tab.dataset.stream)));
      const matches = cases.filter(card => tags(card, "categories").includes(tab.dataset.stream) && intersects(selectedIndustries, tags(card, "industries"))).length;
      tab.querySelector(".stream-tab-count").textContent = matches;
    });
    industryInputs.forEach(input => {
      input.checked = selectedIndustries.has(input.dataset.industry);
      const matches = cases.filter(card => tags(card, "industries").includes(input.dataset.industry) && intersects(selectedAreas, tags(card, "categories"))).length;
      input.closest("label").querySelector(".industry-count").textContent = matches;
    });
    if (industryToggle) {
      const selection = industryToggle.querySelector(".industry-selected-count");
      selection.textContent = selectedIndustries.size ? String(selectedIndustries.size) : "";
    }
    const total = visibleCases().length;
    if (count) count.textContent = (english ? "Matching cases: " : "Найдено кейсов: ") + total;
    if (empty) empty.hidden = total > 0;
    if (mode) {
      writeFilters(mode, preserveHash);
      if (mode === "push" && catalogue && controls) requestAnimationFrame(() => {
        if (controls.getBoundingClientRect().top < (topNavigation?.getBoundingClientRect().bottom || 0)) {
          catalogue.scrollIntoView({ behavior: "instant", block: "start" });
        }
      });
    }
  };

  const readFilters = () => {
    const url = new URL(location.href);
    selectedAreas.clear();
    selectedIndustries.clear();
    (url.searchParams.get("areas") || "").split(",").forEach(value => {
      if (streamTabs.some(tab => tab.dataset.stream === value)) selectedAreas.add(value);
    });
    (url.searchParams.get("industries") || "").split(",").forEach(value => {
      if (industryInputs.some(input => input.dataset.industry === value)) selectedIndustries.add(value);
    });
    if (url.hash.startsWith("#stream-")) {
      selectedAreas.clear();
      selectedIndustries.clear();
      const slug = url.hash.slice(8);
      if (streamTabs.some(tab => tab.dataset.stream === slug)) selectedAreas.add(slug);
    }
    applyFilters();
  };

  const ensureCaseVisible = card => {
    if (careerPage || !card.hidden) return;
    selectedAreas.clear();
    selectedIndustries.clear();
    selectedAreas.add(tags(card, "categories")[0]);
    applyFilters("replace", true);
  };

  streamTabs.forEach(tab => tab.addEventListener("click", () => {
    const slug = tab.dataset.stream;
    if (selectedAreas.has(slug)) selectedAreas.delete(slug);
    else selectedAreas.add(slug);
    applyFilters("push");
    track("stream_select", { stream: [...selectedAreas].join(",") });
  }));
  industryInputs.forEach(input => input.addEventListener("change", () => {
    if (input.checked) selectedIndustries.add(input.dataset.industry);
    else selectedIndustries.delete(input.dataset.industry);
    applyFilters("push");
    track("industry_select", { industry: [...selectedIndustries].join(",") });
  }));
  const resetFilters = () => {
    selectedAreas.clear();
    selectedIndustries.clear();
    applyFilters("push");
    streamTabs[0]?.focus();
  };
  document.querySelector("[data-reset-filters]")?.addEventListener("click", resetFilters);
  document.querySelectorAll('.nav-links a[href="#services"]').forEach(link => link.addEventListener("click", event => {
    event.preventDefault();
    resetFilters();
    catalogue?.scrollIntoView({ behavior: "instant", block: "start" });
  }));
  streamHook = (slug, doScroll) => {
    if (slug === null) readFilters();
    else {
      selectedAreas.clear();
      selectedIndustries.clear();
      if (streamTabs.some(tab => tab.dataset.stream === slug)) selectedAreas.add(slug);
      applyFilters();
    }
    if (doScroll) catalogue?.scrollIntoView({ behavior: "instant", block: "start" });
  };
  readFilters();
  window.addEventListener("popstate", readFilters);

  const modal = document.getElementById("caseModal");

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
    let returnUrl = window.location.pathname + window.location.search;

    const streamOf = (card) => tags(card, "categories")[0] || "";
    const siblings = () => visibleCases();
    const labelOf = (slug) => document.querySelector(`.stream-tab[data-stream="${slug}"] .stream-tab-name`)?.textContent.trim() || ({
      strategy: english ? "Strategy and growth" : "Стратегия и рост",
      transformation: english ? "Transformation" : "Трансформация",
      efficiency: english ? "Operational efficiency" : "Операционная эффективность",
      deals: english ? "Deals and investment" : "Сделки и инвестиции"
    }[slug] || "");

    const fill = (card, addHistoryEntry) => {
      current = card;
      const slug = streamOf(card);
      slots.stream.textContent = tags(card, "categories").map(labelOf).join(" / ");
      slots.kicker.textContent = card.querySelector(".case-kicker")?.textContent.trim() || "";
      slots.title.textContent = card.querySelector(".case-title")?.textContent.trim() || "";
      slots.context.textContent = "";
      slots.context.hidden = true;
      const claims = card.querySelector(".claim-stack");
      slots.claims.innerHTML = claims ? claims.innerHTML : "";
      slots.claims.hidden = !claims;
      const facts = card.querySelector(".project-facts");
      slots.facts.innerHTML = facts ? facts.innerHTML : "";
      slots.facts.classList.toggle("project-facts--star", Boolean(facts?.classList.contains("project-facts--star")));
      slots.facts.querySelectorAll("[id]").forEach((node) => {
        const old = node.id;
        node.id = `m-${old}`;
        slots.facts.querySelectorAll(`[aria-describedby="${old}"]`)
          .forEach((ref) => ref.setAttribute("aria-describedby", `m-${old}`));
      });
      const list = siblings(card);
      const index = list.indexOf(card);
      prevButton.disabled = index <= 0;
      nextButton.disabled = index < 0 || index >= list.length - 1;
      if (inner) inner.scrollTop = 0;
      try {
        if (window.location.hash !== `#${card.id}`) {
          if (addHistoryEntry) history.pushState(null, "", `#${card.id}`);
          else history.replaceState(null, "", `#${card.id}`);
        }
      } catch (_) {
        // Адресная строка не критична для работы окна
      }
    };

    const openCase = (card, scrollToStream = false) => {
      if (modal.open && current === card) return;
      const slug = streamOf(card);
      const fresh = !modal.open;
      ensureCaseVisible(card);
      if (!careerPage) writeFilters("replace", true);
      if (scrollToStream) {
        document.getElementById("services")?.scrollIntoView({ behavior: "instant", block: "start" });
      }
      if (!modal.open) {
        returnUrl = window.location.pathname + window.location.search + (careerPage ? window.location.hash : "#services");
        if (careerPage && returnUrl.includes("#case-")) returnUrl = window.location.pathname + window.location.search + "#projects";
        opener = document.activeElement === document.body
          ? card.querySelector("summary")
          : document.activeElement;
        modal.showModal();
      }
      const wasOpen = !fresh;
      fill(card, fresh);
      track("case_open", { case: card.id, stream: slug });
      if (wasOpen) {
        slots.title.tabIndex = -1;
        slots.title.focus();
      } else {
        modal.querySelector(".case-modal-close")?.focus();
      }
    };
    caseHook = openCase;
    // Прямые ссылки раскрывают ту же краткую карточку на текущей странице.
    if (location.hash.startsWith("#case-")) openHashTarget(false);

    document.querySelectorAll("a[href^='#case-']").forEach((link) => {
      link.addEventListener("click", (event) => {
        if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        const target = document.getElementById(link.getAttribute("href").slice(1));
        const card = target?.dataset.caseTarget ? document.getElementById(target.dataset.caseTarget) : target;
        if (!card?.classList.contains("case-card")) return;
        event.preventDefault();
        openCase(card);
      });
    });

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
        if (copying) copying.then(() => report(english ? "Link copied" : "Ссылка скопирована"), () => report(english ? "Copy the address from your browser" : "Скопируйте адрес из строки браузера"));
        else report(english ? "Copy the address from your browser" : "Скопируйте адрес из строки браузера");
      });
    }

    modal.addEventListener("keydown", (event) => {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      if (event.target.closest("a[href],button:not([disabled])")) return;
      event.preventDefault();
      step(event.key === "ArrowLeft" ? -1 : 1);
    });
    const closeCase = () => {
      if (!modal.open) return;
      try {
        if (current && window.location.hash === `#${current.id}`) {
          history.replaceState(null, "", returnUrl);
        }
      } catch (_) {
        // Адресная строка не критична для работы окна
      }
      const focusTarget = opener?.getClientRects().length
        ? opener
        : document.querySelector(`.stream-tab[data-stream="${current ? streamOf(current) : "strategy"}"]`);
      modal.close();
      opener = null;
      current = null;
      focusTarget?.focus();
    };
    modal.addEventListener("cancel", event => {
      event.preventDefault();
      closeCase();
    });
    modal.querySelector(".case-modal-close")?.addEventListener("click", () => closeCase());
    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeCase();
    });
    window.addEventListener("popstate", () => {
      if (modal.open && !cases.some((card) => window.location.hash === `#${card.id}`)) closeCase();
    });

  }

  document.querySelectorAll(".faq details").forEach((item, index) => {
    item.addEventListener("toggle", () => {
      if (item.open) track("faq_open", { item: index + 1 });
    });
  });
})();
