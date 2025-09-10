# Manual Accessibility Testing Guide

## Overview

This guide provides step-by-step instructions for manually testing the accessibility of the StorySign Platform. Manual testing is essential to ensure that automated tests don't miss real-world accessibility issues.

## Testing Environment Setup

### Required Tools

1. **Screen Readers**

   - Windows: NVDA (free) or JAWS (paid)
   - macOS: VoiceOver (built-in)
   - Linux: Orca (free)

2. **Browser Extensions**

   - axe DevTools
   - WAVE Web Accessibility Evaluator
   - Lighthouse (built-in Chrome)

3. **Color Testing Tools**
   - WebAIM Contrast Checker
   - Colour Contrast Analyser (CCA)

### Browser Settings

- Enable high contrast mode (if available)
- Test with zoom levels: 100%, 200%, 400%
- Test with reduced motion enabled
- Test with JavaScript disabled (basic functionality)

## Screen Reader Testing

### VoiceOver (macOS) Setup

1. System Preferences → Accessibility → VoiceOver
2. Enable VoiceOver (Cmd + F5)
3. Open VoiceOver Utility for settings

**Basic Commands:**

- Navigate: VO + Arrow keys
- Interact: VO + Shift + Down
- Stop interacting: VO + Shift + Up
- Read all: VO + A
- Navigate by headings: VO + Cmd + H

### NVDA (Windows) Setup

1. Download from nvaccess.org
2. Install and run NVDA
3. Configure speech rate and voice

**Basic Commands:**

- Navigate: Arrow keys
- Browse mode: Automatic
- Focus mode: NVDA + Space
- Read all: NVDA + Down Arrow
- Navigate by headings: H
- Navigate by links: K
- Navigate by buttons: B

### Testing Checklist

#### Page Structure

- [ ] Page title is announced correctly
- [ ] Main landmarks are identified (banner, navigation, main, contentinfo)
- [ ] Heading structure is logical (h1 → h2 → h3, no skipped levels)
- [ ] Lists are properly announced
- [ ] Tables have proper headers

#### Navigation

- [ ] Skip links are available and functional
- [ ] All navigation items are announced
- [ ] Current page/section is indicated
- [ ] Breadcrumbs work correctly
- [ ] Search functionality is accessible

#### Forms

- [ ] All form fields have labels
- [ ] Required fields are indicated
- [ ] Error messages are announced
- [ ] Help text is associated with fields
- [ ] Form submission feedback is provided

#### Interactive Elements

- [ ] All buttons have accessible names
- [ ] Link purposes are clear
- [ ] Modal dialogs are announced properly
- [ ] Loading states are communicated
- [ ] Progress indicators work correctly

#### Dynamic Content

- [ ] Live regions announce updates
- [ ] AJAX content changes are announced
- [ ] Error messages are announced immediately
- [ ] Success messages are communicated

## Keyboard Navigation Testing

### Testing Process

1. Disconnect mouse/trackpad
2. Use only keyboard for navigation
3. Test all functionality

### Key Combinations to Test

- **Tab**: Move forward through focusable elements
- **Shift + Tab**: Move backward through focusable elements
- **Enter**: Activate buttons and links
- **Space**: Activate buttons, check checkboxes
- **Arrow keys**: Navigate within components (menus, tabs, etc.)
- **Escape**: Close modals, cancel actions
- **Home/End**: Navigate to beginning/end of lists or content

### Testing Checklist

#### Focus Management

- [ ] Focus indicators are visible and meet contrast requirements
- [ ] Tab order is logical and intuitive
- [ ] Focus doesn't get trapped (except in modals)
- [ ] Focus is restored after modal closes
- [ ] Skip links allow bypassing repetitive content

#### Interactive Elements

- [ ] All buttons are keyboard accessible
- [ ] All links can be activated with keyboard
- [ ] Form controls work with keyboard
- [ ] Custom components respond to appropriate keys
- [ ] Dropdown menus work with arrow keys

#### Modal and Dialog Testing

- [ ] Focus moves to modal when opened
- [ ] Focus is trapped within modal
- [ ] Escape key closes modal
- [ ] Focus returns to trigger element when closed

## Color and Contrast Testing

### Automated Testing

1. Use WebAIM Contrast Checker
2. Test all text/background combinations
3. Verify minimum ratios:
   - Normal text: 4.5:1 (AA), 7:1 (AAA)
   - Large text: 3:1 (AA), 4.5:1 (AAA)
   - UI components: 3:1

### Manual Testing

1. **Grayscale Test**: Convert page to grayscale to check if information is conveyed without color
2. **High Contrast Mode**: Test with system high contrast settings
3. **Color Blindness Simulation**: Use tools to simulate different types of color blindness

### Testing Checklist

- [ ] All text meets contrast requirements
- [ ] Focus indicators meet contrast requirements
- [ ] Error states don't rely solely on color
- [ ] Success states don't rely solely on color
- [ ] Interactive elements are distinguishable
- [ ] Charts and graphs have alternative indicators

## Responsive and Mobile Testing

### Testing Viewports

- Mobile: 320px - 768px
- Tablet: 768px - 1024px
- Desktop: 1024px+

### Testing Checklist

- [ ] Content reflows properly at all sizes
- [ ] Touch targets are at least 44x44px
- [ ] No horizontal scrolling at 320px width
- [ ] Text remains readable when zoomed to 200%
- [ ] All functionality available on mobile
- [ ] Orientation changes work correctly

## User Workflow Testing

### Complete User Journeys

#### Registration and Login

1. Navigate to registration page
2. Fill out form using only keyboard
3. Submit form and handle validation errors
4. Complete registration process
5. Log in with new account
6. Verify all steps are accessible

**Test with screen reader:**

- [ ] Form labels are announced
- [ ] Validation errors are announced
- [ ] Success messages are communicated
- [ ] Loading states are indicated

#### ASL World Module

1. Navigate to ASL World
2. Test connection status announcements
3. Use webcam controls with keyboard
4. Generate story using keyboard only
5. Navigate through practice session
6. Verify feedback is accessible

**Test with screen reader:**

- [ ] Video status changes are announced
- [ ] Story content is readable
- [ ] Practice instructions are clear
- [ ] Feedback is communicated effectively

#### Harmony Module

1. Navigate to Harmony module
2. Start emotion practice session
3. Use controls with keyboard only
4. Complete session and review results
5. Navigate back to main menu

**Test with screen reader:**

- [ ] Session instructions are clear
- [ ] Progress updates are announced
- [ ] Results are communicated effectively

### Error Handling Testing

1. Disconnect internet connection
2. Try to use features that require connection
3. Verify error messages are accessible
4. Test recovery procedures

**Checklist:**

- [ ] Error messages are announced immediately
- [ ] Recovery instructions are provided
- [ ] Retry mechanisms are accessible
- [ ] Error states don't break navigation

## Performance and Motion Testing

### Reduced Motion Testing

1. Enable "Reduce motion" in system preferences
2. Navigate through the application
3. Verify animations are reduced or disabled

**Checklist:**

- [ ] Animations respect reduced motion preference
- [ ] Essential motion is preserved
- [ ] No auto-playing videos with sound
- [ ] Parallax effects are disabled

### Performance Testing

1. Test on slower devices/connections
2. Verify loading states are accessible
3. Check timeout handling

**Checklist:**

- [ ] Loading states are announced
- [ ] Timeouts are communicated
- [ ] Progressive enhancement works
- [ ] Core functionality available without JavaScript

## Documentation and Reporting

### Test Report Template

```markdown
# Accessibility Test Report

## Test Information

- Date: [Date]
- Tester: [Name]
- Platform: [OS/Browser]
- Assistive Technology: [Screen reader/version]

## Summary

- Total Issues Found: [Number]
- Critical Issues: [Number]
- Major Issues: [Number]
- Minor Issues: [Number]

## Issues Found

### Issue 1: [Title]

- **Severity**: Critical/Major/Minor
- **Location**: [Page/Component]
- **Description**: [Detailed description]
- **Steps to Reproduce**:
  1. [Step 1]
  2. [Step 2]
- **Expected Behavior**: [What should happen]
- **Actual Behavior**: [What actually happens]
- **WCAG Guideline**: [Relevant guideline]
- **Recommendation**: [How to fix]

## Positive Findings

- [List things that work well]

## Recommendations

- [Overall recommendations for improvement]
```

### Issue Severity Guidelines

**Critical Issues:**

- Complete inability to access core functionality
- Keyboard traps that prevent navigation
- Missing form labels on required fields
- Insufficient color contrast on essential text

**Major Issues:**

- Difficulty accessing important functionality
- Missing error announcements
- Poor focus management
- Inadequate alternative text for informative images

**Minor Issues:**

- Inconsistent interaction patterns
- Missing helpful descriptions
- Suboptimal but functional accessibility features

## Testing Schedule

### Regular Testing

- **Daily**: Automated accessibility tests in CI/CD
- **Weekly**: Manual keyboard navigation testing
- **Monthly**: Complete screen reader testing
- **Quarterly**: Full accessibility audit with external tools

### Release Testing

- Complete manual testing before each release
- User acceptance testing with assistive technology users
- Performance testing on various devices
- Cross-browser compatibility testing

## Training and Resources

### Team Training Topics

1. Screen reader basics and testing
2. Keyboard navigation patterns
3. ARIA best practices
4. Color and contrast requirements
5. Mobile accessibility considerations

### Recommended Training Resources

- WebAIM Screen Reader Testing Guide
- Deque University courses
- A11y Project resources
- WCAG 2.1 Quick Reference

## Continuous Improvement

### Feedback Collection

- User feedback forms accessible to assistive technology users
- Regular surveys with disability community
- Analytics on accessibility feature usage
- Monitoring of accessibility-related support requests

### Process Improvement

- Regular review of testing procedures
- Updates based on new WCAG guidelines
- Integration of new testing tools
- Team retrospectives on accessibility practices

Remember: Manual testing should complement, not replace, automated testing. Both are essential for comprehensive accessibility assurance.
