import streamlit as st
from bs4 import BeautifulSoup
import re
import requests
import json

# Precompile regular expressions for US to UK conversion
conversion_patterns = []


def load_us_to_uk_dict_from_github(url):
    global conversion_patterns
    response = requests.get(url)
    if response.status_code == 200:
        us_to_uk_dict = json.loads(response.text)
        for us, uk in us_to_uk_dict.items():
            pattern = re.compile(r'\b{}\b'.format(re.escape(us)), flags=re.IGNORECASE)
            conversion_patterns.append((pattern, uk))
        return us_to_uk_dict
    else:
        st.error("Failed to retrieve the dictionary file.")
        return None


@st.cache_data
def convert_us_to_uk(text):
    for pattern, uk in conversion_patterns:
        text = pattern.sub(uk, text)
    return text


def format_html_bold_list(item_text):
    """Format list items in HTML to be bold if they contain a colon."""
    pattern = re.compile(r'(^[^:]+:)')  # Match content containing a colon at the start
    result = pattern.sub(r'<strong>\1</strong>', item_text)
    return result


def process_html(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')

    # Process each paragraph tag
    for p_tag in soup.find_all('p'):
        paragraph_text = p_tag.get_text()
        paragraph_text = convert_us_to_uk(paragraph_text)  # Removed us_to_uk from here

        # Split paragraph into sentences and wrap each sentence in a <p> tag
        sentences = re.split(r'(?<=\.)\s*', paragraph_text)
        new_paragraph = ''.join([f'<p>{sentence.strip()}</p>' for sentence in sentences if sentence.strip()])

        # Replace original paragraph with new content
        p_tag.replace_with(BeautifulSoup(new_paragraph, 'html.parser'))

    # Remove specific headers
    for header in soup.find_all(['h2', 'h3']):
        if "Write the Input in the language of British UK:" in header.get_text() or "Output:" in header.get_text():
            header.decompose()

    # Process ul and ol list items
    for li_tag in soup.find_all('li'):
        item_text = li_tag.get_text()
        formatted_text = format_html_bold_list(item_text)
        if item_text != formatted_text:
            new_content = BeautifulSoup(formatted_text, 'html.parser')
            li_tag.clear()
            li_tag.append(new_content)

    # Convert the soup object back to string
    return str(soup)


def main():
    st.title("HTML Content Processor")

    # New URL for the US to UK conversion dictionary
    us_to_uk_url = 'https://raw.githubusercontent.com/markuskempus/StreamlitTextSplitApp/main/us_to_uk_dictionary.json'
    us_to_uk_dict = load_us_to_uk_dict_from_github(us_to_uk_url)

    # Check if the dictionary is loaded successfully
    if not us_to_uk_dict:
        st.error("Failed to load the US to UK conversion dictionary. Please try again later.")
        return

    # Text area for user to paste HTML content, with a unique key
    html_input = st.text_area("Paste your HTML content here:", height=300, key="html_input")

    # Button to process HTML
    if st.button("Process HTML"):
        processed_html = process_html(html_input)  # Removed us_to_uk_dict from here
        st.markdown("## Processed HTML:")
        st.markdown(processed_html, unsafe_allow_html=True)

        # Adding a text area to copy the processed HTML
        st.text_area("Copy Processed HTML Below:", processed_html, height=300, key="processed_html_output")


if __name__ == "__main__":
    main()
