import os
import re
import sys
import bibtexparser
from collections import defaultdict

def extract_citation_keys(tex_directory):
    citation_keys = set()
    # Pattern to match all \cite commands
    cite_pattern = re.compile(r'\\cite[a-zA-Z]*\*?{([^}]+)}')
    for root, _, files in os.walk(tex_directory):
        for filename in files:
            if filename.endswith('.tex'):
                filepath = os.path.join(root, filename)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    matches = cite_pattern.findall(content)
                    for match in matches:
                        keys = [key.strip() for key in match.split(',')]
                        citation_keys.update(keys)
    return citation_keys

def read_bib_files(bib_directory):
    all_entries = {}
    for filename in os.listdir(bib_directory):
        if filename.endswith('.bib'):
            filepath = os.path.join(bib_directory, filename)
            with open(filepath, 'r', encoding='utf-8') as bib_file:
                bib_database = bibtexparser.load(bib_file)
                for entry in bib_database.entries:
                    entry_id = entry['ID']
                    if entry_id not in all_entries:
                        all_entries[entry_id] = entry
                    else:
                        print(f"Duplicate entry ID '{entry_id}' found in {filename}, ignoring duplicate.")
    return list(all_entries.values())

def correct_capitalization(entry):
    # Correct capitalization for 'title' field
    if 'title' in entry:
        entry['title'] = title_case(entry['title'])
    # Correct capitalization for 'author' field
    if 'author' in entry:
        entry['author'] = standardize_authors(entry['author'])

def title_case(title):
    small_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor',
                   'on', 'at', 'to', 'from', 'by', 'of', 'in', 'out', 'over',
                   'with', 'is', 'ok', 'as', 'if', 'be', 'into', 'than', 'that'}
    # Regular expression to split the title into words and LaTeX commands/braces
    pattern = re.compile(r'(\\[a-zA-Z]+\{.*?\}|{.*?}|[^\s]+)')
    tokens = pattern.findall(title)
    new_title_parts = []
    num_tokens = len(tokens)
    for i, token in enumerate(tokens):
        if token.startswith('\\') or (token.startswith('{') and token.endswith('}')):
            # LaTeX command or group, leave as is
            new_title_parts.append(token)
        else:
            word = token
            if word.isupper():
                # Leave words in all caps as is
                new_word = word
            else:
                # Decide whether to capitalize
                if i == 0 or i == num_tokens - 1:
                    # Always capitalize first and last word
                    new_word = word.capitalize()
                elif word.lower() in small_words:
                    new_word = word.lower()
                else:
                    new_word = word.capitalize()
            new_title_parts.append(new_word)
    new_title = ' '.join(new_title_parts)
    return new_title

def standardize_authors(author_field):
    # Split authors and standardize names as "Last Name, First Name"
    authors = re.split(r'\s+and\s+', author_field)
    standardized_authors = []
    for author in authors:
        author = author.strip()
        if ',' in author:
            # Already in "Last, First" format
            parts = [part.strip() for part in author.split(',', 1)]
            last_name = parts[0]
            first_names = parts[1] if len(parts) > 1 else ''
        else:
            # Split names assuming "First Middle Last" format
            names = author.split()
            if len(names) > 1:
                first_names = ' '.join(names[:-1])
                last_name = names[-1]
            else:
                # Single name, treat as last name
                first_names = ''
                last_name = names[0]
        # Capitalize names properly
        last_name = last_name.capitalize()
        first_names = ' '.join([name.capitalize() for name in first_names.split()])
        if first_names:
            standardized_author = f"{last_name}, {first_names}"
        else:
            standardized_author = last_name
        standardized_authors.append(standardized_author)
    return ' and '.join(standardized_authors)

def detect_booktitle_discrepancies(entries):
    booktitle_variations = defaultdict(set)
    for entry in entries:
        if 'booktitle' in entry:
            normalized_name = re.sub(r'[.,]', '', entry['booktitle'].lower().strip())
            booktitle_variations[normalized_name].add(entry['booktitle'])
        elif 'journal' in entry:
            normalized_name = re.sub(r'[.,]', '', entry['journal'].lower().strip())
            booktitle_variations[normalized_name].add(entry['journal'])
    discrepancies = []
    for variations in booktitle_variations.values():
        if len(variations) > 1:
            discrepancies.append(variations)
    return discrepancies

def collect_unique_fields(entries):
    booktitles = set()
    publishers = set()
    journals = set()
    for entry in entries:
        if 'booktitle' in entry:
            booktitles.add(entry['booktitle'])
        if 'publisher' in entry:
            publishers.add(entry['publisher'])
        if 'journal' in entry:
            journals.add(entry['journal'])
    return booktitles, publishers, journals

def check_required_fields(entry, required_fields, missing_fields_report):
    missing_fields = []
    for field in required_fields:
        if field not in entry:
            entry[field] = ''  # Add missing field with empty value
            missing_fields.append(field)
    if missing_fields:
        missing_fields_report.append({
            'ID': entry['ID'],
            'ENTRYTYPE': entry['ENTRYTYPE'],
            'missing_fields': missing_fields
        })

def unify_entry_fields(entries):
    # Collect all fields used in each category
    category_fields = defaultdict(set)
    for entry in entries:
        entry_type = entry.get('ENTRYTYPE', '').lower()
        fields = set(entry.keys()) - {'ID', 'ENTRYTYPE'}
        category_fields[entry_type].update(fields)
    # Ensure each entry has all fields for its category
    for entry in entries:
        entry_type = entry.get('ENTRYTYPE', '').lower()
        all_fields = category_fields[entry_type]
        for field in all_fields:
            if field not in entry:
                entry[field] = ''  # Add missing field with empty value
    return category_fields

def separate_entries(entries, citation_keys):
    used_entries = []
    unused_entries = []
    for entry in entries:
        if entry['ID'] in citation_keys:
            used_entries.append(entry)
        else:
            unused_entries.append(entry)
    return used_entries, unused_entries

def sort_entries(entries):
    grouped_entries = defaultdict(list)
    for entry in entries:
        entry_type = entry.get('ENTRYTYPE', 'misc').lower()
        grouped_entries[entry_type].append(entry)
    # Define the desired type order
    type_order = ['inproceedings', 'article', 'proceedings', 'book', 'misc']
    remaining_types = sorted(set(grouped_entries.keys()) - set(type_order))
    full_type_order = type_order + remaining_types
    sorted_entries = []
    for entry_type in full_type_order:
        entries_of_type = grouped_entries.get(entry_type, [])
        entries_of_type.sort(key=lambda e: e.get('title', '').lower())
        sorted_entries.extend(entries_of_type)
    return sorted_entries

def write_bib_file(output_path, used_entries, unused_entries, discrepancies, missing_fields_report, booktitles, publishers, journals, category_fields):
    writer = bibtexparser.bwriter.BibTexWriter()
    writer.indent = '    '
    with open(output_path, 'w', encoding='utf-8') as bib_file:
        bib_file.write('USED BIBS\n\n')
        if used_entries:
            used_db = bibtexparser.bibdatabase.BibDatabase()
            used_db.entries = used_entries
            bib_file.write(writer.write(used_db))
        bib_file.write('\n% ------below here is unused\n\n')
        bib_file.write('UNUSED BIBS\n\n')
        if unused_entries:
            unused_db = bibtexparser.bibdatabase.BibDatabase()
            unused_db.entries = unused_entries
            bib_file.write(writer.write(unused_db))
        if discrepancies:
            bib_file.write('\n% Discrepancies in booktitle/journal names:\n\n')
            for variation_set in discrepancies:
                bib_file.write('% Variations found:\n')
                for variation in variation_set:
                    bib_file.write(f'% - {variation}\n')
                bib_file.write('\n')
        if missing_fields_report:
            bib_file.write('\n% Entries with missing required fields:\n\n')
            for report in missing_fields_report:
                bib_file.write(f"% Entry ID: {report['ID']}\n")
                bib_file.write(f"% Entry Type: {report['ENTRYTYPE']}\n")
                bib_file.write(f"% Missing Fields: {', '.join(report['missing_fields'])}\n\n")
        # Print lists of booktitles, publishers, and journals
        bib_file.write('\n% List of booktitles:\n')
        for booktitle in sorted(booktitles):
            bib_file.write(f'% - {booktitle}\n')
        bib_file.write('\n% List of publishers:\n')
        for publisher in sorted(publishers):
            bib_file.write(f'% - {publisher}\n')
        bib_file.write('\n% List of journals:\n')
        for journal in sorted(journals):
            bib_file.write(f'% - {journal}\n')
        # Print category fields
        bib_file.write('\n% Fields used in each category:\n')
        for entry_type, fields in category_fields.items():
            bib_file.write(f'% Entry Type: {entry_type}\n')
            bib_file.write(f'% Fields: {", ".join(sorted(fields))}\n\n')

def main(project_directory):
    sections_dir = os.path.join(project_directory, 'sections')
    citation_keys = extract_citation_keys(sections_dir)
    all_entries = read_bib_files(project_directory)
    # Correct capitalization
    for entry in all_entries:
        correct_capitalization(entry)
    # Unify entry fields within each category
    category_fields = unify_entry_fields(all_entries)
    # Detect discrepancies
    discrepancies = detect_booktitle_discrepancies(all_entries)
    # Collect unique booktitles, publishers, and journals
    booktitles, publishers, journals = collect_unique_fields(all_entries)
    # Check for missing required fields and add them if missing
    missing_fields_report = []
    required_fields_mapping = {
        'article': ['author', 'title', 'journal', 'year', 'doi'],
        'inproceedings': ['author', 'title', 'booktitle', 'year', 'doi'],
        'proceedings': ['editor', 'title', 'year'],
        'book': ['author', 'title', 'publisher', 'year'],
        'misc': ['author', 'title', 'howpublished', 'year'],
        # Add other entry types and their required fields as needed
    }
    for entry in all_entries:
        entry_type = entry.get('ENTRYTYPE', '').lower()
        required_fields = required_fields_mapping.get(entry_type, [])
        check_required_fields(entry, required_fields, missing_fields_report)
    used_entries, unused_entries = separate_entries(all_entries, citation_keys)
    used_entries = sort_entries(used_entries)
    unused_entries = sort_entries(unused_entries)
    output_bib_path = os.path.join(project_directory, 'sorted_references.bib')
    write_bib_file(output_bib_path, used_entries, unused_entries, discrepancies, missing_fields_report, booktitles, publishers, journals, category_fields)
    print(f'Processed bibliography saved to {output_bib_path}')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python script_name.py /path/to/project_directory')
    else:
        main(sys.argv[1])
