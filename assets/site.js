(() => {
  "use strict";

  const root = document.documentElement;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const revealItems = [...document.querySelectorAll(".reveal")];

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

  const progress = document.getElementById("progress");
  const contact = document.getElementById("contact");
  const navLinks = [...document.querySelectorAll(".nav-links a[href^='#']")];
  const navSections = navLinks
    .map((link) => ({ link, section: document.querySelector(link.getAttribute("href")) }))
    .filter((item) => item.section);
  let scrollFrame = 0;

  const updateScrollState = () => {
    const page = document.documentElement;
    const available = Math.max(1, page.scrollHeight - page.clientHeight);
    if (progress) progress.style.transform = `scaleX(${page.scrollTop / available})`;

    const marker = page.scrollTop + 96;
    let current = null;
    navSections.forEach((item) => {
      if (item.section.offsetTop <= marker) current = item;
    });
    if (contact && contact.offsetTop <= marker) current = null;
    navLinks.forEach((link) => {
      const active = current && current.link === link;
      link.classList.toggle("active", Boolean(active));
      if (active) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
    scrollFrame = 0;
  };

  window.addEventListener("scroll", () => {
    if (scrollFrame) return;
    scrollFrame = window.requestAnimationFrame(updateScrollState);
  }, { passive: true });
  updateScrollState();

  const menuButton = document.querySelector(".nav-menu");
  const menu = document.getElementById("navmenu");
  if (menuButton && menu) {
    const setMenu = (open) => {
      menu.classList.toggle("open", open);
      menuButton.setAttribute("aria-expanded", String(open));
      menuButton.setAttribute("aria-label", open ? "Закрыть меню" : "Открыть меню");
    };
    menuButton.addEventListener("click", () => setMenu(!menu.classList.contains("open")));
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

  const openHashTarget = (scrollToTarget = false) => {
    if (!window.location.hash || window.location.hash.length < 2) return;
    const target = document.querySelector(window.location.hash);
    if (!target) return;
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
    const blockers = [heroCta, contact].filter(Boolean);
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
  window.addEventListener("scroll", hideTooltip, { passive: true });

  const track = (name, properties) => {
    try {
      if (typeof window.__track === "function") window.__track(name, properties);
      window.dispatchEvent(new CustomEvent("portfolio:track", {
        detail: { name, properties }
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
  document.querySelectorAll("details.service").forEach((item) => {
    item.addEventListener("toggle", () => {
      if (item.open) track("service_open", { service: item.id });
    });
  });
  document.querySelectorAll("details.project-row").forEach((item) => {
    item.addEventListener("toggle", () => {
      if (item.open) track("project_open", { project: item.id });
    });
  });
  document.querySelectorAll("details.other-work").forEach((item) => {
    item.addEventListener("toggle", () => {
      if (item.open) track("other_work_open", { service: item.closest("details.service")?.id || "" });
    });
  });
  document.querySelectorAll(".faq details").forEach((item, index) => {
    item.addEventListener("toggle", () => {
      if (item.open) track("faq_open", { item: index + 1 });
    });
  });
})();
