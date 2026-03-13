import os
import re

# Точный путь к твоей золотой жиле
base_dir = "/Users/sa/rh.1/docs/restore/1"
output_dir = "~/rh.1/docs_extracted"

os.makedirs(output_dir, exist_ok=True)

def clean_html(raw_html):
    # Грубая очистка: удаляем скрипты, стили и HTML теги
    text = re.sub(r'<script.*?>.*?</script>', '', raw_html, flags=re.DOTALL)
    text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<.*?>', ' ', text)
    # Убираем лишние пробелы и пустые строки
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines)

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file == 'index.html':
            # Имя компонента берем из названия папки (например, blur, camera)
            component_name = os.path.basename(root)
            if not component_name: continue
            
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = clean_html(f.read())
            
            out_path = os.path.join(output_dir, f"{component_name}.txt")
            with open(out_path, 'w', encoding='utf-8') as out_f:
                out_f.write(content)

print(f"Готово! Все компоненты извлечены в папку {output_dir}")