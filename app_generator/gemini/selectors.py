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
    ("css selector", 'button[aria-label*="upload"]'),
    ("css selector", 'button[aria-label*="Upload"]'),
    ("css selector", 'button[data-test-id*="upload"]'),
    (
        "xpath",
        '//button[.//mat-icon[normalize-space()="add"] or .//*[normalize-space()="+"]]',
    ),
)
CONVERSATION_UPLOAD_ACTION = (
    ("xpath", '//*[self::button or @role="menuitem"][contains(normalize-space(.), "Upload files")]'),
    ("css selector", '[role="menuitem"][aria-label*="Upload files"]'),
    ("css selector", 'button[aria-label*="Upload files"]'),
    (
        "xpath",
        '//*[@role="menuitem"][contains(translate(normalize-space(.), '
        '"ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "upload")]',
    ),
    (
        "xpath",
        '//button[contains(translate(normalize-space(.), '
        '"ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "upload from computer")]',
    ),
)
CONVERSATION_FILE_INPUT = (
    ("css selector", 'input[type="file"][accept*="application/pdf"]'),
    ("css selector", 'input[type="file"][accept*=".pdf"]'),
    ("css selector", 'input[type="file"]'),
)
ATTACHMENT_PREVIEW = (
    ("css selector", "uploader-file-preview"),
)
ATTACHMENT_LOADING = (
    ("css selector", "uploader-file-preview .gem-attachment-content.loading"),
    ("css selector", 'uploader-file-preview mat-spinner[aria-label="Loading attachment"]'),
)
ATTACHMENT_READY = (
    ("css selector", "uploader-file-preview .gem-attachment-text"),
    ("css selector", "uploader-file-preview .gem-attachment-extension-label"),
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
GENERATION_ACTIVE = (
    ("css selector", 'button[aria-label*="Stop response"]'),
    ("css selector", 'button[aria-label*="Stop generating"]'),
    ("css selector", 'button[aria-label^="Stop"]'),
    ("css selector", 'button[data-test-id*="stop"]'),
    ("css selector", 'model-response[aria-busy="true"]'),
    ("css selector", '[data-message-author-role="model"][aria-busy="true"]'),
    (
        "xpath",
        '//button[.//mat-icon[normalize-space()="stop"] or '
        './/*[contains(translate(normalize-space(.), "STOP", "stop"), "stop")]]',
    ),
)
RESPONSE_COMPLETE = (
    ("css selector", 'model-response button[aria-label*="Copy"]'),
    ("css selector", '[data-message-author-role="model"] button[aria-label*="Copy"]'),
    ("css selector", 'model-response button[aria-label*="Good response"]'),
    ("css selector", 'model-response button[aria-label*="Bad response"]'),
    ("css selector", 'model-response [data-test-id*="copy"]'),
    ("css selector", 'model-response response-footer'),
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
    ("css selector", "model-response"),
    ("css selector", "model-response message-content"),
    ("css selector", '[data-message-author-role="model"] message-content'),
    ("css selector", ".model-response-text"),
    ("css selector", '[data-test-id*="model-response"]'),
    ("css selector", '[aria-label*="Gemini response"]'),
    (
        "xpath",
        '//message-content[not(ancestor::user-query) and '
        'not(ancestor::*[@data-message-author-role="user"])]',
    ),
    ("css selector", "model-response .markdown"),
)
USER_MESSAGES = (
    ("css selector", '[data-message-author-role="user"]'),
    ("css selector", 'user-query'),
    ("css selector", '[aria-label*="You said"]'),
)
