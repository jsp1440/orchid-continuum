#!/usr/bin/env python3
"""
Orchid Mahjong Tile Designer
Creates beautiful orchid-themed Mahjong tiles for the game
"""

import os
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

class OrchidMahjongTiles:
    def __init__(self):
        self.tile_size = (60, 80)  # Standard Mahjong tile proportions
        self.orchid_suits = {
            'cattleya': {
                'color': '#9B59B6',
                'symbols': ['🌺', '🌸', '🌼', '🌻', '🌷', '🌹', '🥀', '🌾', '🏵️'],
                'name': 'Cattleya'
            },
            'dendrobium': {
                'color': '#3498DB', 
                'symbols': ['💐', '🌿', '🍀', '🌱', '🌲', '🌳', '🌴', '🎋', '🌵'],
                'name': 'Dendrobium'
            },
            'phalaenopsis': {
                'color': '#E91E63',
                'symbols': ['🦋', '🐛', '🐝', '🐞', '🕷️', '🦗', '🐜', '🐌', '🪲'],
                'name': 'Phalaenopsis'
            }
        }
        
        # Honor tiles (wind directions) - AOS Awards
        self.honor_tiles = {
            'aos_awards': {
                'AM': {'name': 'Award of Merit', 'color': '#F39C12'},
                'FCC': {'name': 'First Class Certificate', 'color': '#E74C3C'},
                'HCC': {'name': 'Highly Commended', 'color': '#27AE60'},
                'CBR': {'name': 'Certificate Botanical Recognition', 'color': '#8E44AD'}
            }
        }
        
        # Dragon tiles - Orchid Growing Conditions
        self.dragon_tiles = {
            'growing_conditions': {
                'TEMP': {'name': 'Temperature', 'symbol': '🌡️', 'color': '#E67E22'},
                'LIGHT': {'name': 'Light', 'symbol': '☀️', 'color': '#F1C40F'},
                'WATER': {'name': 'Water', 'symbol': '💧', 'color': '#3498DB'}
            }
        }
        
    def create_tile_design(self, suit, number=None, tile_type='number'):
        """Create a beautiful orchid-themed tile design"""
        
        # Create base tile image
        img = Image.new('RGB', self.tile_size, '#F8F9FA')
        draw = ImageDraw.Draw(img)
        
        # Draw tile border
        border_color = '#2C3E50'
        draw.rectangle([0, 0, self.tile_size[0]-1, self.tile_size[1]-1], 
                      outline=border_color, width=2)
        
        # Draw inner decorative border
        draw.rectangle([3, 3, self.tile_size[0]-4, self.tile_size[1]-4], 
                      outline='#BDC3C7', width=1)
        
        if tile_type == 'number':
            self._draw_number_tile(draw, suit, number)
        elif tile_type == 'honor':
            self._draw_honor_tile(draw, suit)
        elif tile_type == 'dragon':
            self._draw_dragon_tile(draw, suit)
            
        return img
    
    def _draw_number_tile(self, draw, suit, number):
        """Draw numbered tiles with orchid symbols"""
        suit_info = self.orchid_suits[suit]
        
        # Draw suit color background
        draw.rectangle([5, 5, self.tile_size[0]-6, 20], 
                      fill=suit_info['color'], outline=None)
        
        # Draw suit name (small text)
        try:
            font_small = ImageFont.truetype("arial.ttf", 8)
        except:
            font_small = ImageFont.load_default()
            
        text_width = draw.textlength(suit_info['name'], font=font_small)
        draw.text((self.tile_size[0]//2 - text_width//2, 7), 
                 suit_info['name'], fill='white', font=font_small)
        
        # Draw large number in center
        try:
            font_large = ImageFont.truetype("arial.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            
        number_str = str(number)
        text_width = draw.textlength(number_str, font=font_large)
        draw.text((self.tile_size[0]//2 - text_width//2, 30), 
                 number_str, fill=suit_info['color'], font=font_large)
        
        # Draw orchid symbols around the number
        if number <= len(suit_info['symbols']):
            symbol = suit_info['symbols'][number-1]
            try:
                font_symbol = ImageFont.truetype("arial.ttf", 12)
            except:
                font_symbol = ImageFont.load_default()
                
            # Top symbol
            symbol_width = draw.textlength(symbol, font=font_symbol)
            draw.text((self.tile_size[0]//2 - symbol_width//2, 58), 
                     symbol, font=font_symbol)
    
    def _draw_honor_tile(self, draw, award_type):
        """Draw honor tiles with AOS awards"""
        award_info = self.honor_tiles['aos_awards'][award_type]
        
        # Draw background
        draw.rectangle([5, 5, self.tile_size[0]-6, self.tile_size[1]-6], 
                      fill=award_info['color'], outline=None)
        
        # Draw award abbreviation
        try:
            font_large = ImageFont.truetype("arial.ttf", 16)
            font_small = ImageFont.truetype("arial.ttf", 8)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            
        text_width = draw.textlength(award_type, font=font_large)
        draw.text((self.tile_size[0]//2 - text_width//2, 25), 
                 award_type, fill='white', font=font_large)
        
        # Draw full name (wrapped)
        name_parts = award_info['name'].split(' ')
        y_pos = 45
        for part in name_parts:
            text_width = draw.textlength(part, font=font_small)
            draw.text((self.tile_size[0]//2 - text_width//2, y_pos), 
                     part, fill='white', font=font_small)
            y_pos += 10
    
    def _draw_dragon_tile(self, draw, condition_type):
        """Draw dragon tiles with growing conditions"""
        condition_info = self.dragon_tiles['growing_conditions'][condition_type]
        
        # Draw background
        draw.rectangle([5, 5, self.tile_size[0]-6, self.tile_size[1]-6], 
                      fill=condition_info['color'], outline=None)
        
        # Draw symbol
        try:
            font_large = ImageFont.truetype("arial.ttf", 20)
            font_small = ImageFont.truetype("arial.ttf", 8)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            
        symbol = condition_info['symbol']
        symbol_width = draw.textlength(symbol, font=font_large)
        draw.text((self.tile_size[0]//2 - symbol_width//2, 20), 
                 symbol, font=font_large)
        
        # Draw condition name
        name = condition_info['name']
        text_width = draw.textlength(name, font=font_small)
        draw.text((self.tile_size[0]//2 - text_width//2, 50), 
                 name, fill='white', font=font_small)
    
    def generate_complete_tile_set(self):
        """Generate complete Mahjong tile set with orchid theme"""
        tiles = {}
        
        # Generate number tiles (1-9 for each suit)
        for suit_name in self.orchid_suits.keys():
            tiles[suit_name] = {}
            for number in range(1, 10):
                tile_img = self.create_tile_design(suit_name, number, 'number')
                tiles[suit_name][number] = tile_img
        
        # Generate honor tiles (AOS awards)
        tiles['honors'] = {}
        for award in self.honor_tiles['aos_awards'].keys():
            tile_img = self.create_tile_design(award, tile_type='honor')
            tiles['honors'][award] = tile_img
        
        # Generate dragon tiles (growing conditions)
        tiles['dragons'] = {}
        for condition in self.dragon_tiles['growing_conditions'].keys():
            tile_img = self.create_tile_design(condition, tile_type='dragon')
            tiles['dragons'][condition] = tile_img
        
        return tiles
    
    def save_tiles_as_sprites(self, output_dir='static/images/mahjong_tiles'):
        """Save all tiles as individual sprite files"""
        os.makedirs(output_dir, exist_ok=True)
        
        tiles = self.generate_complete_tile_set()
        
        # Save number tiles
        for suit_name, suit_tiles in tiles.items():
            if suit_name in ['honors', 'dragons']:
                continue
            for number, tile_img in suit_tiles.items():
                filename = f"{suit_name}_{number}.png"
                tile_img.save(os.path.join(output_dir, filename))
        
        # Save honor tiles
        for award, tile_img in tiles['honors'].items():
            filename = f"honor_{award}.png"
            tile_img.save(os.path.join(output_dir, filename))
        
        # Save dragon tiles
        for condition, tile_img in tiles['dragons'].items():
            filename = f"dragon_{condition}.png"
            tile_img.save(os.path.join(output_dir, filename))
        
        print(f"✅ Generated {self._count_total_tiles(tiles)} orchid Mahjong tiles")
        return output_dir
    
    def _count_total_tiles(self, tiles):
        """Count total number of tiles generated"""
        count = 0
        for suit_name, suit_tiles in tiles.items():
            if isinstance(suit_tiles, dict):
                count += len(suit_tiles)
        return count
    
    def get_tile_data_for_game(self):
        """Get tile data structure for game logic"""
        return {
            'suits': list(self.orchid_suits.keys()),
            'honors': list(self.honor_tiles['aos_awards'].keys()),
            'dragons': list(self.dragon_tiles['growing_conditions'].keys()),
            'numbers_per_suit': 9,
            'total_tiles': 3 * 9 + 4 + 3  # 3 suits × 9 numbers + 4 honors + 3 dragons
        }

def main():
    """Generate orchid Mahjong tiles"""
    tile_designer = OrchidMahjongTiles()
    
    # Create tiles directory
    output_dir = tile_designer.save_tiles_as_sprites()
    
    # Get game data
    tile_data = tile_designer.get_tile_data_for_game()
    
    print("🎴 Orchid Mahjong Tile System Created!")
    print(f"📁 Tiles saved to: {output_dir}")
    print(f"🌺 {tile_data['total_tiles']} unique tile designs")
    print(f"🎋 Suits: {', '.join(tile_data['suits'])}")
    print(f"🏆 Honor tiles: {', '.join(tile_data['honors'])}")
    print(f"🐉 Dragon tiles: {', '.join(tile_data['dragons'])}")

if __name__ == "__main__":
    main()