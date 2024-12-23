import os
import re
import bibtexparser
from collections import defaultdict

conference_format_mapping = {
    'CVPR': {
        'article':       ['author', 'title', 'journal', 'year'],
        'inproceedings': ['author', 'title', 'booktitle', 'year'],
        'book':          ['author', 'title', 'publisher', 'year'],
        'misc':          ['author', 'title', 'year', 'howpublished'],
        'arxiv':         ['author', 'title', 'journal', 'year'],
    },
    'CHI': {
        'article':       ['author', 'title', 'journal', 'volume', 'number', 'year', 'address', 'publisher'],
        'inproceedings': ['author', 'title', 'booktitle', 'year', 'address', 'publisher', 'pages'],
        'book':          ['author', 'title', 'year', 'address', 'publisher'],
        'misc':          ['author', 'title', 'howpublished', 'year'],
        'arxiv':         ['author', 'title', 'journal', 'year'],
    },
}

def extract_citation_keys(tex_files):
    citation_keys = set()
    # Pattern to match all \cite commands
    cite_pattern = re.compile(r'\\cite[a-zA-Z]*\*?{([^}]+)}')

    for filepath in tex_files:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            matches = cite_pattern.findall(content)
            for match in matches:
                keys = [key.strip() for key in match.split(',')]
                citation_keys.update(keys)
    return citation_keys

def read_bib_files(bib_directory, bib_filename):
    all_entries = {}
    for filename in os.listdir(bib_directory):
        if filename.endswith(bib_filename):
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
    # if 'author' in entry:
    #     entry['author'] = standardize_authors(entry['author'])

def title_case(title):
    # List of lowercase words that shouldn't be capitalized unless they're the first or last word
    lowercase_words = {"with", "a", "an", "and", "as", "at", "but", "by", "for", "in", "nor", "of", "on", "or", "so", "the", "to", "up", "yet"}
    
    # Split the title into words
    words = title.split()
    
    # Capitalize each word according to title case rules, preserving original capitalization
    title_cased_words = [
        word if (i != 0 and i != len(words) - 1 and word.lower() in lowercase_words) else word[0].upper() + word[1:]
        for i, word in enumerate(words)
    ]
    
    # Join the words back into a single string
    return ' '.join(title_cased_words)


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

def determine_arxiv(entry):
    for field in entry:
        if 'arxiv' in entry[field].lower():
            return True
    return False

def check_required_fields(entry, required_fields, missing_fields_report):
    # Remove fields that are not in required_fields
    fields_to_remove = [field for field in entry if field not in required_fields and field not in {'ID', 'ENTRYTYPE'}]
    for field in fields_to_remove:
        del entry[field]
    
    # Check for missing required fields and add them with empty values
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

    # Sort entries within each type by title
    sorted_groups = {}
    for entry_type in full_type_order:
        entries_of_type = grouped_entries.get(entry_type, [])
        entries_of_type.sort(key=lambda e: e.get('title', '').lower())
        sorted_groups[entry_type] = entries_of_type
    
    return sorted_groups


def write_bib_file(output_path, used_entries, discrepancies, missing_fields_report, booktitles, publishers, journals, category_fields):
    writer = bibtexparser.bwriter.BibTexWriter()
    writer.indent = '    '
    with open(output_path, 'w', encoding='utf-8') as bib_file:
        if used_entries:
            for entry_type, entries in used_entries.items():
                bib_file.write(f'% {entry_type.upper()}\n\n')
                used_db = bibtexparser.bibdatabase.BibDatabase()
                used_db.entries = entries
                bib_file.write(writer.write(used_db))
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

def find_tex_files(folder_path):
    tex_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.tex'):
                tex_files.append(os.path.join(root, file))
    return tex_files

def main(args):
    project_directory = os.path.join("projects",args.project_directory)
    bib_filename = args.bib_file
    tex_files = find_tex_files(project_directory)
    citation_keys = extract_citation_keys(tex_files)
    all_entries = read_bib_files(project_directory, bib_filename)

    for entry in all_entries:
        correct_capitalization(entry)

    category_fields = unify_entry_fields(all_entries)
    discrepancies = detect_booktitle_discrepancies(all_entries)
    booktitles, publishers, journals = collect_unique_fields(all_entries)
    missing_fields_report = []
    required_fields_mapping = conference_format_mapping[args.conference]
    for entry in all_entries:
        entry_type = entry.get('ENTRYTYPE', '').lower()
        if entry_type == 'misc' and determine_arxiv(entry):
            required_fields = required_fields_mapping.get('arxiv', [])
        else:
            required_fields = required_fields_mapping.get(entry_type, [])
        check_required_fields(entry, required_fields, missing_fields_report)

    used_entries, unused_entries = separate_entries(all_entries, citation_keys)
    used_entries = sort_entries(used_entries)
    unused_entries = sort_entries(unused_entries)
    used_output_bib_path = os.path.join(project_directory, 'used_sorted_references.bib')
    unused_output_bib_path = os.path.join(project_directory, 'unused_sorted_references.bib')
    write_bib_file(used_output_bib_path, used_entries, discrepancies, missing_fields_report, booktitles, publishers, journals, category_fields)
    write_bib_file(unused_output_bib_path, unused_entries, discrepancies, missing_fields_report, booktitles, publishers, journals, category_fields)
    print(f'Processed bibliography saved to {used_output_bib_path} and {unused_output_bib_path}')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Sort and clean bibliography entries based on citation keys in LaTeX files.')
    parser.add_argument('--project_directory', help='Path to the directory containing LaTeX files and bibliography files.')
    # specify bib file directory
    parser.add_argument('--bib_file', help='Name of the directory containing bibliography files.', default='reference.bib')
    parser.add_argument('--conference', help='Conference name (e.g., CVPR, CHI).', default='CHI', choices=conference_format_mapping.keys())
    args = parser.parse_args()
    main(args)
