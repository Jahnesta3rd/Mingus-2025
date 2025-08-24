import pytest


@pytest.mark.selenium
@pytest.mark.parametrize("size", [
    (1400, 900),  # desktop
    (1024, 768),  # tablet landscape
    (768, 1024),  # tablet portrait
    (414, 896),   # large phone
    (375, 812),   # iPhone X
    (360, 740),   # small Android
])
def test_responsive_layout(driver, base_url, size):
    width, height = size
    driver.set_window_size(width, height)
    driver.get(base_url)

    # Sanity: page loads and has main content
    assert driver.find_elements("css selector", "main, #app, .container")


