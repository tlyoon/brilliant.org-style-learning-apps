"""Centralized accessible selectors for Gemini UI variants."""

NAME_FIELD = (
    ("css selector", 'input[aria-label="Name"]'),
    ("css selector", 'input[placeholder*="Name"]'),
    ("xpath", '//label[contains(normalize-space(.), "Name")]/following::input[1]'),
)
EDIT_GEM_BUTTON = (
    ("xpath", '//button[contains(normalize-space(.), "Edit Gem")]'),
    ("xpath", '//a[contains(normalize-space(.), "Edit Gem")]'),
    ("css selector", 'button[aria-label*="Edit Gem"]'),
    ("css selector", 'a[aria-label*="Edit Gem"]'),
)
DESCRIPTION_FIELD = (
    ("css selector", 'textarea[aria-label*="Description"]'),
    ("css selector", '[contenteditable="true"][aria-label*="Description"]'),
    ("xpath", '//label[contains(normalize-space(.), "Description")]/following::*[self::textarea or @contenteditable="true"][1]'),
)
INSTRUCTIONS_FIELD = (
    ("css selector", 'textarea[aria-label*="Instructions"]'),
    ("css selector", '[contenteditable="true"][aria-label*="Instructions"]'),
    ("xpath", '//label[contains(normalize-space(.), "Instructions")]/following::*[self::textarea or @contenteditable="true"][1]'),
)
SAVE_BUTTON = (
    ("xpath", '//button[normalize-space()="Update" or normalize-space()="Save"]'),
    ("css selector", 'button[aria-label="Update"]'),
    ("css selector", 'button[aria-label="Save"]'),
)
ATTACH_BUTTON = (
    ("xpath", '//button[contains(normalize-space(.), "Add files")]'),
    ("css selector", 'button[aria-label*="Add files"]'),
    ("css selector", 'button[aria-label*="Attach"]'),
)
CONVERSATION_UPLOAD_ACTION = (
    ("xpath", '//*[self::button or @role="menuitem"][contains(normalize-space(.), "Upload files")]'),
    ("css selector", '[role="menuitem"][aria-label*="Upload files"]'),
    ("css selector", 'button[aria-label*="Upload files"]'),
)
CONVERSATION_FILE_INPUT = (
    ("css selector", 'input[type="file"]'),
)
ATTACHMENT_LABELS = (
    ("css selector", '[data-test*="attachment"]'),
    ("css selector", '[aria-label*="attachment"]'),
    ("css selector", 'mat-chip'),
)
ATTACHMENT_PROCESSING = (
    ("css selector", '[aria-label*="uploading"]'),
    ("css selector", '[aria-label*="processing"]'),
    ("xpath", '//*[contains(translate(normalize-space(.), "PROCESSINGUPLOADING", "processinguploading"), "processing")]'),
    ("xpath", '//*[contains(translate(normalize-space(.), "PROCESSINGUPLOADING", "processinguploading"), "uploading")]'),
)
NEW_CHAT_BUTTON = (
    ("css selector", 'button[aria-label*="New chat"]'),
    ("css selector", 'a[aria-label*="New chat"]'),
    ("xpath", '//*[self::button or self::a][contains(normalize-space(.), "New chat")]'),
)
COMPOSER = (
    ("css selector", 'textarea[aria-label*="prompt"]'),
    ("css selector", 'div[contenteditable="true"][role="textbox"]'),
    ("css selector", 'textarea[placeholder*="Ask"]'),
)
SEND_BUTTON = (
    ("css selector", 'button[aria-label*="Send"]'),
    ("xpath", '//button[contains(translate(@aria-label, "SEND", "send"), "send")]'),
)
MODEL_SELECTOR = (
    ("css selector", 'button[aria-label*="model"]'),
    ("css selector", '[role="button"][aria-haspopup="menu"][aria-label*="Model"]'),
)
MODEL_OPTIONS = (
    ("css selector", '[role="menuitem"]'),
    ("css selector", '[role="option"]'),
    ("css selector", '[role="listbox"] [role="listitem"]'),
)
MODEL_RESPONSES = (
    ("css selector", '[data-message-author-role="model"]'),
    ("css selector", 'message-content'),
    ("css selector", '[aria-label*="Gemini response"]'),
)
