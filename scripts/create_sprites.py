"""
Demo-Spritesheet Generator für Der Alchemist
Erstellt ein einfaches Test-Spritesheet falls keine wizard_char.png vorhanden ist
"""
import pygame
import math

def create_demo_spritesheet():
    """Erstellt ein einfaches animiertes Spritesheet für Tests"""
    pygame.init()
    
    # Spritesheet Konfiguration
    num_frames = 60
    frame_width = 32
    frame_height = 48
    sheet_width = num_frames * frame_width
    sheet_height = frame_height
    
    # Erstelle Spritesheet Surface
    spritesheet = pygame.Surface((sheet_width, sheet_height), pygame.SRCALPHA)
    spritesheet.fill((0, 0, 0, 0))  # Transparent
    
    print(f"🎬 Erstelle Demo-Spritesheet: {sheet_width}x{sheet_height}")
    print(f"📐 {num_frames} Frames à {frame_width}x{frame_height}")
    
    for frame in range(num_frames):
        x = frame * frame_width
        
        # Basis-Charakter (Alchemist)
        # Körper (Robe)
        body_color = (50 + int(20 * math.sin(frame * 0.2)), 50, 150)  # Leicht animierte Farbe
        pygame.draw.rect(spritesheet, body_color, 
                        (x + 8, 20, 16, 20))
        
        # Kopf
        skin_color = (255, 220, 177)
        pygame.draw.circle(spritesheet, skin_color, 
                          (x + 16, 15), 8)
        
        # Hut (Animation durch leichte Bewegung)
        hat_offset = int(2 * math.sin(frame * 0.3))
        hat_color = (100, 50, 200)
        hat_points = [
            (x + 8, 10 + hat_offset),
            (x + 24, 10 + hat_offset), 
            (x + 16, 2 + hat_offset)
        ]
        pygame.draw.polygon(spritesheet, hat_color, hat_points)
        
        # Augen
        eye_color = (0, 0, 0)
        pygame.draw.circle(spritesheet, eye_color, (x + 12, 13), 1)
        pygame.draw.circle(spritesheet, eye_color, (x + 20, 13), 1)
        
        # Arme (leichte Bewegung)
        arm_offset = int(3 * math.sin(frame * 0.4))
        # Linker Arm
        pygame.draw.circle(spritesheet, skin_color, (x + 6, 25 + arm_offset), 3)
        # Rechter Arm  
        pygame.draw.circle(spritesheet, skin_color, (x + 26, 25 - arm_offset), 3)
        
        # Zauberstab (nur in rechter Hand, manche Frames)
        if frame % 10 < 7:  # Zauberstab ist nicht immer sichtbar
            staff_color = (139, 69, 19)  # Braun
            pygame.draw.line(spritesheet, staff_color, 
                           (x + 26, 25 - arm_offset), 
                           (x + 30, 15 - arm_offset), 2)
            # Magischer Kristall am Ende
            crystal_color = (255, 0, 255)
            pygame.draw.circle(spritesheet, crystal_color, 
                             (x + 30, 15 - arm_offset), 2)
        
        # Beine (einfache Animation)
        leg_offset = int(2 * math.sin(frame * 0.5))
        pygame.draw.rect(spritesheet, body_color, 
                        (x + 10, 40, 4, 8 + leg_offset))
        pygame.draw.rect(spritesheet, body_color, 
                        (x + 18, 40, 4, 8 - leg_offset))
    
    # Speichere Spritesheet
    pygame.image.save(spritesheet, 'assets/wizard_char_demo.png')
    print("✅ Demo-Spritesheet erstellt: assets/wizard_char_demo.png")
    
    return spritesheet

def create_simple_static_sprite():
    """Erstellt einen einfachen statischen Sprite als Fallback"""
    pygame.init()
    
    sprite_size = 64
    sprite = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    
    # Alchemist Design
    # Robe
    pygame.draw.rect(sprite, (50, 50, 150), (16, 32, 32, 40))
    # Kopf
    pygame.draw.circle(sprite, (255, 220, 177), (32, 24), 12)
    # Hut
    hat_points = [(16, 20), (48, 20), (32, 8)]
    pygame.draw.polygon(sprite, (100, 50, 200), hat_points)
    # Augen
    pygame.draw.circle(sprite, (0, 0, 0), (28, 22), 2)
    pygame.draw.circle(sprite, (0, 0, 0), (36, 22), 2)
    # Zauberstab
    pygame.draw.line(sprite, (139, 69, 19), (48, 40), (56, 24), 3)
    pygame.draw.circle(sprite, (255, 0, 255), (56, 24), 3)
    
    pygame.image.save(sprite, 'assets/wizard_static.png')
    print("✅ Statischer Sprite erstellt: assets/wizard_static.png")

if __name__ == "__main__":
    print("🎨 Demo-Spritesheet Generator")
    print("=" * 40)
    
    create_demo_spritesheet()
    create_simple_static_sprite()
    
    print("\n🎯 Assets erstellt!")
    print("📁 Verfügbare Sprites:")
    print("   - assets/wizard_char_demo.png (60-Frame Animation)")
    print("   - assets/wizard_static.png (Einzelbild)")
    print("\n💡 Teste mit: python src/enhanced_main.py")
