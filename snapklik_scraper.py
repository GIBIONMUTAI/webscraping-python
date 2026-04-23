import pandas as pd
import re
import webbrowser
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import os
import platform
import subprocess
from collections import Counter

# --- Functions ---
def _extract_field(raw_data_string: str, pattern: str) -> str:
    """Extracts a single field using regex, cleans HTML tags/entities."""
    match = re.search(pattern, raw_data_string, re.DOTALL | re.IGNORECASE)
    if match:
        raw_value = match.group(1).strip()
        return BeautifulSoup(raw_value, 'html.parser').get_text(strip=True).replace('&amp;', '&').strip()
    return 'N/A'

def extract_product_data(raw_data_string: str) -> Dict[str, Any]:
    """Extracts all product data fields from a raw HTML/data string."""
    if not isinstance(raw_data_string, str) or not raw_data_string:
        raise ValueError("Raw data string must be a non-empty string.")

    extracted_data = {}
    extracted_data['Product Name'] = _extract_field(raw_data_string, r'product name(?:\{.*?\})?\s*.*?<h1[^>]*>(.+?)</h1>')
    extracted_data['Product Line Name'] = _extract_field(raw_data_string, r'product line name\s*(<h1.+?</h1>|<p.+?</p>)')
    extracted_data['Brand Name'] = _extract_field(raw_data_string, r'Brand Name <(.+?)/>')
    extracted_data['Product Description'] = _extract_field(raw_data_string, r'Product Description (<li.+?</li>|<p.+?</p>|<span.+?</span>)')
    
    # Extract all image URLs
    image_urls = re.findall(r'<img[^>]+src="([^"]+)"', raw_data_string)
    extracted_data['Product Images'] = image_urls if image_urls else ['N/A']

    extracted_data['Barcode (EAN/UPC)'] = _extract_field(raw_data_string, r'Barcode \(EAN/UPC\)\s*<(.+?)/>')
    extracted_data['Price'] = _extract_field(raw_data_string, r'Price <(.+?)/>')
    extracted_data['Size/Volume'] = _extract_field(raw_data_string, r'Size/Volume </?\s*(.+?)\s*[/]?>')
    extracted_data['Ingredients'] = _extract_field(raw_data_string, r'Ingredients <(.+?)/>')
    extracted_data['Skin Concern'] = _extract_field(raw_data_string, r'Skin Concern\s*<(.+?)/>')
    extracted_data['Source URL'] = _extract_field(raw_data_string, r'Source URL <(.+?)/>')

    # Product ID from Source URL
    source_url = extracted_data.get('Source URL', 'N/A')
    product_id_match = re.search(r'/([^/?]+)[/?]?$', source_url)
    extracted_data['Product ID'] = product_id_match.group(1) if product_id_match else 'N/A'

    return extracted_data

def export_to_excel(data: List[Dict[str, Any]], filename: str = "products_data.xlsx") -> None:
    """Exports product data to Excel and opens it automatically."""
    if not data:
        print("No data provided for Excel export. Skipping.")
        return

    try:
        df = pd.DataFrame(data)
        excel_columns = [
            'Product ID', 'Product Name', 'Product Line Name', 'Brand Name',
            'Product Description', 'Product Images', 'Barcode (EAN/UPC)',
            'Price', 'Size/Volume', 'Ingredients', 'Skin Concern', 'Source URL'
        ]
        df = df.reindex(columns=excel_columns)
        df.to_excel(filename, index=False)
        print(f"Product data successfully exported to '{filename}'.")

        # Open Excel automatically
        if platform.system() == "Windows":
            os.startfile(filename)
        elif platform.system() == "Darwin":
            subprocess.call(["open", filename])
        else:
            subprocess.call(["xdg-open", filename])

    except Exception as e:
        print(f"An error occurred during Excel export: {e}")

def open_images_in_browser(products_data: List[Dict[str, Any]]):
    """Opens all product images in browser tabs."""
    print("\nOpening all product images in your browser...")
    for product in products_data:
        image_urls = product.get('Product Images', [])
        for image_url in image_urls:
            if image_url != 'N/A':
                try:
                    webbrowser.open(image_url)
                except Exception as e:
                    print(f"Could not open image URL {image_url}: {e}")

def extract_shared_ingredients(products_data: List[Dict[str, Any]]) -> None:
    """Identifies ingredients that appear in 2 or more products and saves to Excel."""
    all_ingredients = []

    for product in products_data:
        ingredients_str = product.get('Ingredients', '')
        if ingredients_str != 'N/A':
            # Convert string like "['A','B','C']" to list of stripped ingredients
            ingredients_list = re.findall(r"'(.*?)'", ingredients_str)
            all_ingredients.extend(ingredients_list)

    # Count occurrences
    ingredient_counts = Counter(all_ingredients)
    shared_ingredients = {ing: count for ing, count in ingredient_counts.items() if count >= 2}

    if shared_ingredients:
        df_shared = pd.DataFrame(
            shared_ingredients.items(),
            columns=['Ingredient', 'Number of Products Containing']
        )
        shared_filename = "shared_ingredients.xlsx"
        df_shared.to_excel(shared_filename, index=False)
        print(f"Shared ingredients exported to '{shared_filename}'.")
        # Open automatically
        if platform.system() == "Windows":
            os.startfile(shared_filename)
        elif platform.system() == "Darwin":
            subprocess.call(["open", shared_filename])
        else:
            subprocess.call(["xdg-open", shared_filename])
    else:
        print("No shared ingredients found among products.")

# --- Main Execution ---
if __name__ == "__main__":
    raw_product_data_strings = [
        """
        Product Name <Medicube PDRN Caffeine/h1>

        Product line Name <p _ngcontent-ng-c2530449508="" class="mat-headline-5 gray subtitle-font mt_10 mb_0 ng-star-inserted"> Depuffing &amp; Hydration Salmon DNA + Caffeine + Collagen For Refined, Glass Skin &amp; Face Contour Support Korean Skin Care </p>

        Brand Name <Collagen/>


        Product Description <span _ngcontent-ng-c2530449508="" class="fw_500 ng-star-inserted"> | Depuffing &amp; Hydration Salmon DNA + Caffeine + Collagen For Refined, Glass Skin &amp; Face Contour Support Korean Skin Care</span>

        Product Images <img _ngcontent-ng-c4091586270="" loading="eager" referrerpolicy="no-referrer" defaultimage="" style="aspect-ratio: 1 / 1 !important; max-width: 600px;" srcset="https://m.media-amazon.com/images/I/81IunZS-NWL._US300_.jpg 300w,https://m.media-amazon.com/images/I/81IunZS-NWL._US500_.jpg 500w,https://m.media-amazon.com/images/I/81IunZS-NWL._US700_.jpg 700w,https://m.media-amazon.com/images/I/81IunZS-NWL._US900_.jpg 900w,https://m.media-amazon.com/images/I/81IunZS-NWL._US1100_.jpg 1100w,https://m.media-amazon.com/images/I/81IunZS-NWL._US1300_.jpg 1300w,https://m.media-amazon.com/images/I/81IunZS-NWL._US1500_.jpg 1500w" sizes="(max-width: 300px) 100vw, (max-width: 800px) calc(100vw - 200px), 600px" src="https://m.media-amazon.com/images/I/81IunZS-NWL.jpg" alt="undefined" class="full-width ng-star-inserted">
        Barcode (EAN/UPC) <8800289474774/>

        Price <44 USD/>

        Size/Volume </25ml>

        Ingredients <'Hydration Salmon DNA','Caffeine','Collagen'/>


        Skin Concern <reduce puffiness & dullness, promoting a more refreshed, energized look by morning/>

        Source URL <https://snapklik.com/en-ky/product/medicube-pdrn-caffeine-overnight-wrapping-peel-off-facial-mask-firming-depuffing-and-hydration-salmon-dna-caffeine-collagen-for-refined-glass-skin-and-face-contour-support-korean-skin-care/0UVZ4P370ZL85/>
        """,
        """
        product Name <PanOxyl/h1>

        product line Name <h1 _ngcontent-ng-c2530449508="" class="mat-headline-4 title-font ng-star-inserted" style="margin: 7px 0 0;"> Medicube Deep Vita C Facial Pads, Vitamin C Toner Pads For Uneven Skin Tone, 500,000PPM Of Vitamin Water &amp; 3 Types Of Vitamin, Hydrating &amp; Resurfacing </h1>

        Brand Name <Medicube Deep Vita PanOxyl/>


        Product Description <p _ngcontent-ng-c2530449508="" class="mb_0 px_18 fw_600 ng-star-inserted"> Medicube Deep Vita C Facial Pads, Vitamin C Toner Pads For Uneven Skin Tone, 500,000PPM Of Vitamin Water &amp; 3 Types Of Vitamin, Hydrating &amp; Resurfacing <span _ngcontent-ng-c2530449508="" class="fw_500 ng-star-inserted"> | (70 Sheets)</span></p>


        Product Images <img _ngcontent-ng-c3615914110="" fill="" sizes="(max-width:559px) 100vw, (max-width:665px) 300px, (max-width:749px) 350px, (max-width:849px) 250px, (max-width:989px) 300px, (max-width:1159px) 350px, 555px" ngsrcset="300w, 400w, 500w, 600w, 700w, 800w, 900w, 1000w, 1100w, 1200w, 1300w, 1400w, 1500w, 2500w" style="aspect-ratio: 1 / 1 !important; position: absolute; width: 100%; height: 100%; inset: 0px;" alt="Medicube Deep Vita C Facial Pads, Vitamin C Toner Pads For Uneven Skin Tone, 500,000PPM Of Vitamin Water &amp; 3 Types Of Vitamin, Hydrating &amp; Resurfacing view 0" loading="eager" fetchpriority="high" ng-img="true" src="https://m.media-amazon.com/images/I/71QBdNbIPPL._US500_.jpg" srcset="https://m.media-amazon.com/images/I/71QBdNbIPPL._US300_.jpg 300w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US400_.jpg 400w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US500_.jpg 500w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US600_.jpg 600w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US700_.jpg 700w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US800_.jpg 800w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US900_.jpg 900w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1000_.jpg 1000w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1100_.jpg 1100w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1200_.jpg 1200w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1300_.jpg 1300w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1400_.jpg 1400w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1500_.jpg 1500w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US2500_.jpg 2500w">

        Barcode (EAN/UPC) <8800256109661/>

        Price <44 USD/>

        Size/Volume </0.1 kg>

        Ingredients <'Vitamin','Resurfacing'/>


        Skin Concern <effectively swiping away visible dark spots and blemishes/>

        Source URL <https://snapklik.com/en-ky/product/medicube-deep-vita-c-facial-pads-vitamin-c-toner-pads-for-uneven-skin-tone-500000ppm-of-vitamin-water-and-3-types-of-vitamin-hydrating-and-resurfacing-70-sheets/0PZF4PJ7LSWJ5/>
        """,
        """
        Product Name <Medicube Deep Vita C Facial Pads</h1>

        Product line Name <h1 _ngcontent-ng-c2530449508="" class="mat-headline-4 title-font ng-star-inserted" style="margin: 7px 0 0;"> Hydrating Facial Cleanser, Moisturizing Face Wash For Dry Skin, Hyaluronic Acid + Ceramides + Glycerin, Hydrating Cleanser For Normal To Dry Skin, National Eczema Association Certified </h1>0;"> Medicube Deep Vita C Facial Pads, Vitamin C Toner Pads For Uneven Skin Tone, 500,000PPM Of Vitamin Water &amp; 3 Types Of Vitamin, Hydrating &amp; Resurfacing </h1>

        Brand Name <CeraVe/>

        Product Description <li _ngcontent-ng-c1804213653="" class="mat-subtitle-2 ng-star-inserted" style="margin: 10px 0;">[ HYDRATING FACE WASH ] Daily face wash with hyaluronic acid, ceramides, and glycerin to help hydrate skin without stripping moisture. Removes face makeup, dirt, and excess oil, provides 24-hour hydration and leaves a moisturized, non-greasy feel..</li>


        Product Images <img _ngcontent-ng-c3615914110="" fill="" sizes="(max-width:559px) 100vw, (max-width:665px) 300px, (max-width:749px) 350px, (max-width:849px) 250px, (max-width:989px) 300px, (max-width:1159px) 350px, 555px" ngsrcset="300w, 400w, 500w, 600w, 700w, 800w, 900w, 1000w, 1100w, 1200w, 1300w, 1400w, 1500w, 2500w" style="aspect-ratio: 1 / 1 !important; position: absolute; width: 100%; height: 100%; inset: 0px;" alt="Medicube Deep Vita C Facial Pads, Vitamin C Toner Pads For Uneven Skin Tone, 500,000PPM Of Vitamin Water &amp; 3 Types Of Vitamin, Hydrating &amp; Resurfacing view 0" loading="eager" fetchpriority="high" ng-img="true" src="https://m.media-amazon.com/images/I/71QBdNbIPPL._US500_.jpg" srcset="https://m.media-amazon.com/images/I/71QBdNbIPPL._US300_.jpg 300w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US400_.jpg 400w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US500_.jpg 500w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US600_.jpg 600w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US700_.jpg 700w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US800_.jpg 800w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US900_.jpg 900w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1000_.jpg 1000w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1100_.jpg 1100w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1200_.jpg 1200w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1300_.jpg 1300w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1400_.jpg 1400w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US1500_.jpg 1500w, https://m.media-amazon.com/images/I/71QBdNbIPPL._US2500_.jpg 2500w">

        Barcode (EAN/UPC) <3606000534872/>

        Price <49 USD/>

        Size/Volume </0.6 kg>

        Ingredients <'Aqua', 'Water', 'Glycerin', 'dermatologists'/>


        Skin Concern <MULTI-USE GENTLE CLEANSER,HYDRATING FACE WASH/>

        Source URL <https://snapklik.com/en-ky/product/cerave-hydrating-facial-cleanser-moisturizing-face-wash-for-dry-skin-hyaluronic-acid-ceramides-glycerin-hydrating-cleanser-for-normal-to-dry-skin-national-eczema-association-certified/02884PW73SWX5/>

        """,
        """
        Product Name <Handmade Whipped Tallow Balm</h1>

        Product line Name <h1 _ngcontent-ng-c2530449508="" class="mat-headline-4 title-font ng-star-inserted" style="margin: 7px 0 0;"> Hydrating Facial Cleanser, Moisturizing Face Wash For Dry Skin, Hyaluronic Acid + Ceramides + Glycerin, Hydrating Cleanser For Normal To Dry Skin, National Eczema Association Certified </h1>0;"> Medicube Deep Vita C Facial Pads, Vitamin C Toner Pads For Uneven Skin Tone, 500,000PPM Of Vitamin Water &amp; 3 Types Of Vitamin, Hydrating &amp; Resurfacing </h1>

        Brand Name < Large Herb-Infused (Unscented)/>

        Product Description <li _ngcontent-ng-c1804213653="" class="mat-subtitle-2 ng-star-inserted" style="margin: 10px 0;">DO IT LIKE GRANDMA DID: Tallow--or rendered beef fat--is ancestral skincare. Our ancestors relied almost solely on animal fats to moisturize, protect, and heal their skin. Enjoy our light, meltable, whipped tallow balm as a contemporary nod to the practice of our forefathers..</li>

        Product Images <img _ngcontent-ng-c3615914110="" fill="" sizes="(max-width:559px) 100vw, (max-width:665px) 300px, (max-width:749px) 350px, (max-width:849px) 250px, (max-width:989px) 300px, (max-width:1159px) 350px, 555px" ngsrcset="300w, 400w, 500w, 600w, 700w, 800w, 900w, 1000w, 1100w, 1200w, 1300w, 1400w, 1500w, 2500w" style="aspect-ratio: 1 / 1 !important; position: absolute; width: 100%; height: 100%; inset: 0px;" alt="Handmade Whipped Tallow Balm view 1" loading="lazy" fetchpriority="auto" ng-img="true" src="https://m.media-amazon.com/images/I/71A5GIBHiYL._US500_.jpg" srcset="https://m.media-amazon.com/images/I/71A5GIBHiYL._US300_.jpg 300w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US400_.jpg 400w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US500_.jpg 500w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US600_.jpg 600w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US700_.jpg 700w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US800_.jpg 800w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US900_.jpg 900w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US1000_.jpg 1000w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US1100_.jpg 1100w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US1200_.jpg 1200w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US1300_.jpg 1300w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US1400_.jpg 1400w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US1500_.jpg 1500w, https://m.media-amazon.com/images/I/71A5GIBHiYL._US2500_.jpg 2500w">

        Barcode (EAN/UPC) <N/A/>

        Price <79 USD/>

        Size/Volume < 0.1 kg/>

        Ingredients <'Vitamin','stearic','Water' ,'saturated fat'/>


        Skin Concern <nourishing skin/>

        Source URL <https://snapklik.com/en-ky/product/handmade-whipped-tallow-balm-herb-infused-unscented-large-jar-2-6-oz/0U6H4PH7CHF05/>

        """,
        """
        
        Product Name <Hawaiian Tropic After Sun Body Butter</h1>

        Product line Name <p _ngcontent-ng-c2530449508="" class="mat-headline-5 gray subtitle-font mt_10 mb_0 ng-star-inserted"> With Coconut Oil, 8oz Hawaiian Tropic After Sun Lotion, Beach Essentials, Summer Vacation Essentials, Tan Extender Lotion, Coconut Body Butter, 8oz </p>

        Brand Name < Large Herb-Infused (Unscented)/>


        Product Description <li _ngcontent-ng-c1804213653="" class="mat-subtitle-2 ng-star-inserted" style="margin: 10px 0;">ULTRA-RICH MOISTURIZERS leave skin feeling silky-soft, with an indulgent coconut scent that reminds you of a dreamy vacation.</li>
     
        Product Image <img _ngcontent-ng-c3615914110="" fill="" sizes="(max-width:559px) 100vw, (max-width:665px) 300px, (max-width:749px) 350px, (max-width:849px) 250px, (max-width:989px) 300px, (max-width:1159px) 350px, 555px" ngsrcset="300w, 400w, 500w, 600w, 700w, 800w, 900w, 1000w, 1100w, 1200w, 1300w, 1400w, 1500w, 2500w" style="aspect-ratio: 1 / 1 !important; position: absolute; width: 100%; height: 100%; inset: 0px;" alt="Hawaiian Tropic After Sun Body Butter view 1" loading="lazy" fetchpriority="auto" ng-img="true" src="https://m.media-amazon.com/images/I/713NAkf+-gL._US500_.jpg" srcset="https://m.media-amazon.com/images/I/713NAkf+-gL._US300_.jpg 300w, https://m.media-amazon.com/images/I/713NAkf+-gL._US400_.jpg 400w, https://m.media-amazon.com/images/I/713NAkf+-gL._US500_.jpg 500w, https://m.media-amazon.com/images/I/713NAkf+-gL._US600_.jpg 600w, https://m.media-amazon.com/images/I/713NAkf+-gL._US700_.jpg 700w, https://m.media-amazon.com/images/I/713NAkf+-gL._US800_.jpg 800w, https://m.media-amazon.com/images/I/713NAkf+-gL._US900_.jpg 900w, https://m.media-amazon.com/images/I/713NAkf+-gL._US1000_.jpg 1000w, https://m.media-amazon.com/images/I/713NAkf+-gL._US1100_.jpg 1100w, https://m.media-amazon.com/images/I/713NAkf+-gL._US1200_.jpg 1200w, https://m.media-amazon.com/images/I/713NAkf+-gL._US1300_.jpg 1300w, https://m.media-amazon.com/images/I/713NAkf+-gL._US1400_.jpg 1400w, https://m.media-amazon.com/images/I/713NAkf+-gL._US1500_.jpg 1500w, https://m.media-amazon.com/images/I/713NAkf+-gL._US2500_.jpg 2500w">
        
        Barcode (EAN/UPC) < 3337875685894/>
        
        Price <34 USD/>

        Size/Volume < 0.3 kg/>

        Ingredients < 'coconut oil', 'shea butter','Water', 'avocado oil'/>


        Skin Concern <SKIN-NOURISHING AFTER SUN MOISTURIZER/>

        Source URL <https://snapklik.com/en-ky/product/hawaiian-tropic-after-sun-body-butter-with-coconut-oil-8oz-hawaiian-tropic-after-sun-lotion-beach-essentials-summer-vacation-essentials-tan-extender-lotion-coconut-body-butter-8oz/02W44P37CZWP5/>
        """,
        """
        Product Name <Universal Flare Care/>

        Product line Name <h1 _ngcontent-ng-c2530449508="" class="mat-headline-4 title-font ng-star-inserted" style="margin: 7px 0 0;"> Universal Flare Care Relief For 97% Of Skin Issues Cysts, Inflamed Skin, Hidradenitis Suppurativa, Abscesses, Impetigo All Natural Flare Up Solution </h1>

        Brand Name <With Propolis & Egg Yolk Extract 4 Oz/>


        Product Description <li _ngcontent-ng-c1804213653="" class="mat-subtitle-2 ng-star-inserted" style="margin: 10px 0;">MADE FOR 97% OF COMMON SKIN CONCERNS: including boils, Hidradenitis Suppurativa (HS), abscesses, pilonidal cysts, chafing, and more..</li>
	
        Product Image <img _ngcontent-ng-c3615914110="" fill="" sizes="(max-width:559px) 100vw, (max-width:665px) 300px, (max-width:749px) 350px, (max-width:849px) 250px, (max-width:989px) 300px, (max-width:1159px) 350px, 555px" ngsrcset="300w, 400w, 500w, 600w, 700w, 800w, 900w, 1000w, 1100w, 1200w, 1300w, 1400w, 1500w, 2500w" style="aspect-ratio: 1 / 1 !important; position: absolute; width: 100%; height: 100%; inset: 0px;" alt="Universal Flare Care Relief For 97% Of Skin Issues Cysts, Inflamed Skin, Hidradenitis Suppurativa, Abscesses, Impetigo All Natural Flare Up Solution view 0" loading="eager" fetchpriority="high" ng-img="true" src="https://m.media-amazon.com/images/I/81HQyqW8qvL._US500_.jpg" srcset="https://m.media-amazon.com/images/I/81HQyqW8qvL._US300_.jpg 300w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US400_.jpg 400w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US500_.jpg 500w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US600_.jpg 600w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US700_.jpg 700w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US800_.jpg 800w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US900_.jpg 900w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US1000_.jpg 1000w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US1100_.jpg 1100w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US1200_.jpg 1200w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US1300_.jpg 1300w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US1400_.jpg 1400w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US1500_.jpg 1500w, https://m.media-amazon.com/images/I/81HQyqW8qvL._US2500_.jpg 2500w">
        
        Barcode (EAN/UPC) <345334328889/>
        
        Price <74 USD/>

        Size/Volume<N/A/>

        Ingredients < 'shea butter','Water','avocado oil'/>


        Skin Concern <MULTI-STAGE HEALING,CONVENIENT/>

        Source URL <https://snapklik.com/en-ky/product/la-roche-posay-toleriane-purifying-foaming-facial-cleanser-oil-free-face-wash-for-women-and-men-with-niacinamide-ceramides-pore-cleanser-safe-for-sensitive-skin-wont-dry-out-skin-soap-free-200ml/089M4PI7X0J15/>
        """,
        """
        Product Name <Vanicream Daily Facial Moisturizer/>

        Product line Name <p _ngcontent-ng-c2530449508="" class="mat-headline-5 gray subtitle-font mt_10 mb_0 ng-star-inserted"> With Ceramides And Hyaluronic Acid - Formulated Without Common Irritants For Those With Sensitive Skin, 3 Fl Oz (Pack Of 1) </p>
        
        Brand Name <With Propolis & Egg Yolk Extract 4 Oz/>


        Product Description <li _ngcontent-ng-c1804213653="" class="mat-subtitle-2 ng-star-inserted" style="margin: 10px 0;">Sensitive moisturizer: Vanicream fragrance-free daily face moisturizer is a lightweight, gluten-free moisturizer for sensitive skin.</li>
        
        Product Image<img _ngcontent-ng-c4091586270="" loading="eager" referrerpolicy="no-referrer" defaultimage="" style="aspect-ratio: 1 / 1 !important; max-width: 600px;" srcset="https://m.media-amazon.com/images/I/71G1bwds-SL._US300_.jpg 300w,https://m.media-amazon.com/images/I/71G1bwds-SL._US500_.jpg 500w,https://m.media-amazon.com/images/I/71G1bwds-SL._US700_.jpg 700w,https://m.media-amazon.com/images/I/71G1bwds-SL._US900_.jpg 900w,https://m.media-amazon.com/images/I/71G1bwds-SL._US1100_.jpg 1100w,https://m.media-amazon.com/images/I/71G1bwds-SL._US1300_.jpg 1300w,https://m.media-amazon.com/images/I/71G1bwds-SL._US1500_.jpg 1500w" sizes="(max-width: 300px) 100vw, (max-width: 800px) calc(100vw - 200px), 600px" src="https://m.media-amazon.com/images/I/71G1bwds-SL.jpg" alt="undefined" class="full-width ng-star-inserted">
        
        Barcode (EAN/UPC) <	345334329114/>
        
        Price <34 USD/>

        Size/Volume < 89 ml/>
        
        Ingredients < 'Ceramides','Hyaluronic Acid',/>


        Skin Concern <Sensitive moisturize/>

        Source URL <https://snapklik.com/en-ky/product/vanicream-daily-facial-moisturizer-with-ceramides-and-hyaluronic-acid-formulated-without-common-irritants-for-those-with-sensitive-skin-3-fl-oz-pack-of-1/08644PO7RYOP5/>
        """,
        """
        Product Name <THAYERS/>

        product line name <h1 _ngcontent-ng-c2530449508="" class="mat-headline-4 title-font ng-star-inserted" style="margin: 7px 0 0;"> THAYERS Alcohol-Free, Hydrating, Unscented Witch Hazel Facial Toner </h1>
        
        Brand Name <THAYERS-Facial Toner/>


        Product Description <li _ngcontent-ng-c1804213653="" class="mat-subtitle-2 ng-star-inserted" style="margin: 10px 0;">Proven Results: In just one use of this face toner, skin feels nourished, healthier, skin tone appears even, and skin is hydrated all day long. After one week of use, pores look reduced, skin looks clarified, and skin texture looks smoother. Non-comedogenic..</li>
        
        Product Image <img _ngcontent-ng-c3615914110="" fill="" sizes="(max-width:559px) 100vw, (max-width:665px) 300px, (max-width:749px) 350px, (max-width:849px) 250px, (max-width:989px) 300px, (max-width:1159px) 350px, 555px" ngsrcset="300w, 400w, 500w, 600w, 700w, 800w, 900w, 1000w, 1100w, 1200w, 1300w, 1400w, 1500w, 2500w" style="aspect-ratio: 1 / 1 !important; position: absolute; width: 100%; height: 100%; inset: 0px;" alt="THAYERS Alcohol-Free, Hydrating, Unscented Witch Hazel Facial Toner view 0" loading="eager" fetchpriority="high" ng-img="true" src="https://m.media-amazon.com/images/I/61BLQFzKOAL._US500_.jpg" srcset="https://m.media-amazon.com/images/I/61BLQFzKOAL._US300_.jpg 300w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US400_.jpg 400w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US500_.jpg 500w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US600_.jpg 600w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US700_.jpg 700w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US800_.jpg 800w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US900_.jpg 900w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US1000_.jpg 1000w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US1100_.jpg 1100w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US1200_.jpg 1200w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US1300_.jpg 1300w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US1400_.jpg 1400w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US1500_.jpg 1500w, https://m.media-amazon.com/images/I/61BLQFzKOAL._US2500_.jpg 2500w">
        
        Barcode (EAN/UPC) <041507051805/>
        
        Price <34 USD/>

        Size/Volume <0.7 kg/>

        Ingredients <'Aloe Vera'/>


        Skin Concern <skin feels nourished, healthier, skin tone, skin hydrated/>

        Source URL <https://snapklik.com/en-ky/product/thayers-alcohol-free-hydrating-original-witch-hazel-facial-toner-with-aloe-vera-formula-vegan-dermatologist-tested-and-recommended-12-oz-packaging-may-vary/05384PH76H155/>
        """,
        """
        Product Name <SkinSmart/>

        Product line Name <h1 _ngcontent-ng-c2530449508="" class="mat-headline-4 title-font ng-star-inserted" style="margin: 7px 0 0;"> SkinSmart Facial Cleanser For Acne, Targets Bacteria For Active Teenage Athletes Post Workout And Adult Acne, 8 Oz Spray Bottle, Safe For Multiple Daily Uses </h1>
        
        Brand Name <SkinSmart-Antimicrobial/>

        Product Description <li _ngcontent-ng-c1804213653="" class="mat-subtitle-2 ng-star-inserted" style="margin: 10px 0;">In rare cases, a mild stinging sensation may occur. Do not use in case of known hypersensitivity to hypochlorous acid or salt. Actual Product Style and Design may vary..</li>
        
        Product Image <img _ngcontent-ng-c3615914110="" fill="" sizes="(max-width:559px) 100vw, (max-width:665px) 300px, (max-width:749px) 350px, (max-width:849px) 250px, (max-width:989px) 300px, (max-width:1159px) 350px, 555px" ngsrcset="300w, 400w, 500w, 600w, 700w, 800w, 900w, 1000w, 1100w, 1200w, 1300w, 1400w, 1500w, 2500w" style="aspect-ratio: 1 / 1 !important; position: absolute; width: 100%; height: 100%; inset: 0px;" alt="SkinSmart Facial Cleanser For Acne, Targets Bacteria For Active Teenage Athletes Post Workout And Adult Acne, 8 Oz Spray Bottle, Safe For Multiple Daily Uses view 1" loading="lazy" fetchpriority="auto" ng-img="true" src="https://m.media-amazon.com/images/I/81LV9HY5diL._US500_.jpg" srcset="https://m.media-amazon.com/images/I/81LV9HY5diL._US300_.jpg 300w, https://m.media-amazon.com/images/I/81LV9HY5diL._US400_.jpg 400w, https://m.media-amazon.com/images/I/81LV9HY5diL._US500_.jpg 500w, https://m.media-amazon.com/images/I/81LV9HY5diL._US600_.jpg 600w, https://m.media-amazon.com/images/I/81LV9HY5diL._US700_.jpg 700w, https://m.media-amazon.com/images/I/81LV9HY5diL._US800_.jpg 800w, https://m.media-amazon.com/images/I/81LV9HY5diL._US900_.jpg 900w, https://m.media-amazon.com/images/I/81LV9HY5diL._US1000_.jpg 1000w, https://m.media-amazon.com/images/I/81LV9HY5diL._US1100_.jpg 1100w, https://m.media-amazon.com/images/I/81LV9HY5diL._US1200_.jpg 1200w, https://m.media-amazon.com/images/I/81LV9HY5diL._US1300_.jpg 1300w, https://m.media-amazon.com/images/I/81LV9HY5diL._US1400_.jpg 1400w, https://m.media-amazon.com/images/I/81LV9HY5diL._US1500_.jpg 1500w, https://m.media-amazon.com/images/I/81LV9HY5diL._US2500_.jpg 2500w">
        
        Barcode (EAN/UPC) <	854593007157/>
        
        Price <39 USD/>

        Size/Volume <0.2 kg/>

        Ingredients <'Aloe Vera','stearic'/>


        Skin Concern <Removes sweat & dirt, unclog pores; safe for sensitive skin/>

        Source URL <https://snapklik.com/en-ky/product/skinsmart-facial-cleanser-for-acne-targets-bacteria-for-active-teenage-athletes-post-workout-and-adult-acne-8-oz-spray-bottle-safe-for-multiple-daily-uses/02IU4PF72X1D5/>
        """,
        """
        Product name <Naked Tallow Balm/>

        product line name <h1 _ngcontent-ng-c2530449508="" class="mat-headline-4 title-font ng-star-inserted" style="margin: 7px 0 0;"> Beef Tallow For Skin NAKED TALLOW BALM 1 Ingredient - 100% Grass Fed Beef Tallow Beef Tallow For Body &amp; Face Whipped &amp; UNSCENTED For Sensititve Dry Skin, Babies, Eczema, Psoriasis, Rosacea </h1>
        
        Brand Name <re-root Beef Tallow/>

        Product Description <li _ngcontent-ng-c1804213653="" class="mat-subtitle-2 ng-star-inserted" style="margin: 10px 0;">NATURE'S MOLECULAR MARVEL: Embrace the natural potency of tallow, with its perfect balance of vitamins A, D, E, and K, plus essential fatty acids. These bioavailable nutrients support skin health at the cellular level, promoting elasticity, moisture retention, and rejuvenation..</li>
        
        Product Image <img _ngcontent-ng-c3615914110="" fill="" sizes="(max-width:559px) 100vw, (max-width:665px) 300px, (max-width:749px) 350px, (max-width:849px) 250px, (max-width:989px) 300px, (max-width:1159px) 350px, 555px" ngsrcset="300w, 400w, 500w, 600w, 700w, 800w, 900w, 1000w, 1100w, 1200w, 1300w, 1400w, 1500w, 2500w" style="aspect-ratio: 1 / 1 !important; position: absolute; width: 100%; height: 100%; inset: 0px;" alt="Beef Tallow For Skin NAKED TALLOW BALM 1 Ingredient - 100% Grass Fed Beef Tallow Beef Tallow For Body &amp; Face Whipped &amp; UNSCENTED For Sensititve Dry Skin, Babies, Eczema, Psoriasis, Rosacea view 0" loading="eager" fetchpriority="high" ng-img="true" src="https://m.media-amazon.com/images/I/71b8gj8lDTL._US500_.jpg" srcset="https://m.media-amazon.com/images/I/71b8gj8lDTL._US300_.jpg 300w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US400_.jpg 400w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US500_.jpg 500w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US600_.jpg 600w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US700_.jpg 700w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US800_.jpg 800w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US900_.jpg 900w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US1000_.jpg 1000w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US1100_.jpg 1100w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US1200_.jpg 1200w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US1300_.jpg 1300w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US1400_.jpg 1400w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US1500_.jpg 1500w, https://m.media-amazon.com/images/I/71b8gj8lDTL._US2500_.jpg 2500w">
        
        Barcode (EAN/UPC) <	N/A/>
        
        Price <64 USD/>

        Size/Volume <0.2 kg/>

        Ingredients <'vitamins','shea butter','fatty acids'/>


        Skin Concern <hydration Perfect for face, lips, elbows, heel and  gentle makeup remover/>

        Source URL <https://snapklik.com/en-ky/product/beef-tallow-for-skin-naked-tallow-balm-1-ingredient-100-grass-fed-beef-tallow-beef-tallow-for-body-and-face-whipped-and-unscented-for-sensititve-dry-skin-babies-eczema-psoriasis-rosacea-4oz/0I7L4PI7UHOD5/>
        """
    ]

    # Extract all product data
    products_data = []
    for raw in raw_product_data_strings:
        try:
            products_data.append(extract_product_data(raw))
        except Exception as e:
            print(f"Error extracting product data: {e}")

    # Export product data to Excel
    export_to_excel(products_data, filename="products_data.xlsx")

    # Open all product images
    open_images_in_browser(products_data)

    # Extract shared ingredients and export to Excel
    extract_shared_ingredients(products_data)
