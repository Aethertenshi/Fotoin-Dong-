import pygame

class TransformSprite:
    def __init__(self, image_path: str, x: float, y: float):
        """
        Initializes a transformable sprite.
        
        Parameters:
        - image_path: Path to the image file.
        - x: Initial X coordinate (center of the sprite).
        - y: Initial Y coordinate (center of the sprite).
        """
        # Load the image and ensure it has an alpha channel for transparency
        self.original_image = pygame.image.load(image_path).convert_alpha()
        
        self.x = x
        self.y = y
        self.alpha = 255          # Alpha value (0 to 255)
        self.rotation = 0.0        # Rotation in degrees (counter-clockwise)
        self.scale = 1.0           # Scale factor (1.0 is original size)

    def draw(self, screen: pygame.Surface):
        """
        Applies scaling, rotation, and alpha to the original image and draws it
        centered at (self.x, self.y) to prevent off-center wobbling.
        """
        # Get original dimensions
        orig_width, orig_height = self.original_image.get_size()
        
        # Calculate new dimensions based on scale
        new_width = int(orig_width * self.scale)
        new_height = int(orig_height * self.scale)
        
        # Guard against zero or negative dimensions
        if new_width <= 0 or new_height <= 0:
            return

        # 1. Scale the image
        scaled_image = pygame.transform.scale(self.original_image, (new_width, new_height))
        
        # 2. Rotate the image (around its center)
        # Note: pygame.transform.rotate rotates counter-clockwise.
        rotated_image = pygame.transform.rotate(scaled_image, self.rotation)
        
        # 3. Apply Alpha Transparency
        # set_alpha works on surfaces; since rotated_image is a new surface from transform,
        # it is safe to set its alpha directly.
        rotated_image.set_alpha(max(0, min(255, int(self.alpha))))
        
        # 4. Get the rect of the final image and center it at (self.x, self.y)
        # This is critical! A rotated image has a larger bounding box than the original,
        # so aligning by the center prevents the sprite from "wobbling" or shifting position.
        rect = rotated_image.get_rect()
        rect.center = (int(self.x), int(self.y))
        
        # 5. Draw (blit) the image to the screen
        screen.blit(rotated_image, rect.topleft)
