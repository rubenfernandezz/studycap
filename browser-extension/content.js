// Return only the visible caption text and lecture title to the popup.
(() => {
  let lectureTitle = "Untitled Lecture";
  const titleSelectors = [
    ".video-title",
    ".video-title-text",
    "h1",
    ".title-text",
    ".lecture-title"
  ];

  for (const selector of titleSelectors) {
    const titleElement = document.querySelector(selector);
    if (titleElement && titleElement.textContent.trim()) {
      lectureTitle = titleElement.textContent.trim();
      break;
    }
  }


  const captionElements = document.querySelectorAll(".event-tab-scroll-pane .index-event-row .event-text span");
  const captions = Array.from(captionElements, el => el.innerText.trim()).filter(Boolean).join("\n");
  return {title: lectureTitle, captions};
})();
