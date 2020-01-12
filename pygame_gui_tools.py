import pygame
from pygame.surface import Surface
from pygame_gui import UIManager
from pygame_gui.core.drawable_shapes import RoundedRectangleShape
from pygame_gui.elements import UIButton


class NoFrameShape(RoundedRectangleShape):
    def __init__(self, containing_rect: pygame.Rect, theming_parameters, states,
                 manager: UIManager, help_rect):
        self.help_rect = help_rect
        super().__init__(containing_rect, theming_parameters, states, manager)

    def redraw_state(self, state_str):
        print(self.background_rect)

        self.surfaces[state_str] = Surface((self.help_rect.width, self.help_rect.width), pygame.SRCALPHA, 32)
        state_str = state_str
        text_colour_state_str = state_str + '_text'
        image_state_str = state_str + '_image'

        self.rebuild_images_and_text(image_state_str, state_str, text_colour_state_str)


class NoFrameButton(UIButton):
    def rebuild_shape(self):
        theming_parameters = {'normal_bg': self.colours['normal_bg'],
                              'normal_text': self.colours['normal_text'],
                              'normal_border': self.colours['normal_border'],
                              'normal_image': self.normal_image,
                              'hovered_bg': self.colours['hovered_bg'],
                              'hovered_text': self.colours['hovered_text'],
                              'hovered_border': self.colours['hovered_border'],
                              'hovered_image': self.hovered_image,
                              'disabled_bg': self.colours['disabled_bg'],
                              'disabled_text': self.colours['disabled_text'],
                              'disabled_border': self.colours['disabled_border'],
                              'disabled_image': self.disabled_image,
                              'selected_bg': self.colours['selected_bg'],
                              'selected_text': self.colours['selected_text'],
                              'selected_border': self.colours['selected_border'],
                              'selected_image': self.selected_image,
                              'active_bg': self.colours['active_bg'],
                              'active_border': self.colours['active_border'],
                              'active_text': self.colours['active_text'],
                              'active_image': self.selected_image,
                              'border_width': self.border_width,
                              'shadow_width': self.shadow_width,
                              'font': self.font,
                              'text': self.text,
                              'text_horiz_alignment': self.text_horiz_alignment,
                              'text_vert_alignment': self.text_vert_alignment,
                              'text_horiz_alignment_padding': self.text_horiz_alignment_padding,
                              'text_vert_alignment_padding': self.text_vert_alignment_padding,
                              'shape_corner_radius': self.shape_corner_radius}

        self.drawable_shape = NoFrameShape(self.rect, theming_parameters,
                                           ['normal', 'hovered', 'disabled',
                                            'selected', 'active'], self.ui_manager, self.rect)

        self.image = self.drawable_shape.get_surface('normal')
