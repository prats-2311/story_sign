# StorySign Platform Accessibility Guide

## Overview

The StorySign Platform is designed to be fully accessible and compliant with WCAG 2.1 AA standards. This document provides comprehensive guidelines for maintaining and testing accessibility features across the platform.

## Accessibility Standards

### WCAG 2.1 AA Compliance

The platform adheres to the Web Content Accessibility Guidelines (WCAG) 2.1 Level AA, which includes:

- **Perceivable**: Information and UI components must be presentable to users in ways they can perceive
- **Operable**: UI components and navigation must be operable by all users
- **Understandable**: Information and UI operation must be understandable
- **Robust**: Content must be robust enough to be interpreted by assistive technologies

### Key Accessibility Features

#### 1. Keyboard Navigation

- All interactive elements are keyboard accessible
- Logical tab order throughout the application
- Focus indicators meet contrast requirements (3:1 minimum)
- Skip links for efficient navigation
- Focus trapping in modals and dialogs

#### 2. Screen Reader Support

- Semantic HTML structure with proper landmarks
- ARIA labels, roles, and properties where needed
- Live regions for dynamic content announcements
- Alternative text for images and media
- Descriptive link text and button labels

#### 3. Color and Contrast

- Color contrast ratios meet WCAG AA standards (4.5:1 for normal text, 3:1 for large text)
- Information is not conveyed by color alone
- High contrast mode support
- Dark mode with appropriate contrast ratios

#### 4. Responsive Design

- Touch targets meet minimum size requirements (44x44px)
- Content reflows properly at different zoom levels
- Mobile-optimized interactions
- Prevents horizontal scrolling at 320px width

#### 5. Motion and Animation

- Respects `prefers-reduced-motion` settings
- No auto-playing media with sound
- Animations can be paused or disabled
- No content that flashes more than 3 times per second

## Component Accessibility Guidelines

### Buttons

```jsx
// ✅ Good - Accessible button
<Button
  ariaLabel="Save document"
  onClick={handleSave}
  disabled={isLoading}
  loading={isLoading}
>
  Save
</Button>

// ❌ Bad - Missing accessibility features
<div onClick={handleSave}>Save</div>
```

**Requirements:**

- Use semantic `<button>` elements
- Provide `aria-label` for icon-only buttons
- Include loading states with appropriate announcements
- Ensure minimum touch target size (44x44px)

### Forms

```jsx
// ✅ Good - Accessible form field
<FormField
  label="Email Address"
  type="email"
  required
  error={emailError}
  helpText="We'll never share your email"
  value={email}
  onChange={setEmail}
/>

// ❌ Bad - Missing labels and error handling
<input type="email" placeholder="Email" />
```

**Requirements:**

- Associate labels with form controls
- Provide error messages with `role="alert"`
- Use `aria-invalid` for invalid fields
- Include help text with `aria-describedby`
- Group related fields with `<fieldset>` and `<legend>`

### Modals and Dialogs

```jsx
// ✅ Good - Accessible modal
<Modal
  isOpen={isOpen}
  onClose={handleClose}
  title="Confirm Action"
  ariaDescribedBy="modal-description"
  initialFocusRef={cancelButtonRef}
>
  <p id="modal-description">Are you sure you want to delete this item?</p>
  <Button ref={cancelButtonRef} onClick={handleClose}>
    Cancel
  </Button>
  <Button onClick={handleConfirm}>Delete</Button>
</Modal>
```

**Requirements:**

- Use `role="dialog"` and `aria-modal="true"`
- Provide accessible name with `aria-labelledby`
- Trap focus within the modal
- Return focus to trigger element on close
- Close with Escape key

### Live Regions

```jsx
// ✅ Good - Proper announcements
<LiveRegion
  message="Form saved successfully"
  politeness="polite"
/>

<AssertiveLiveRegion
  message="Error: Connection lost"
/>
```

**Requirements:**

- Use appropriate politeness levels (`polite` vs `assertive`)
- Clear messages after appropriate delay
- Don't overuse assertive announcements
- Provide context in announcements

## Testing Guidelines

### Automated Testing

#### Axe Testing

```javascript
import { axe, toHaveNoViolations } from "jest-axe";

test("should not have accessibility violations", async () => {
  const { container } = render(<Component />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

#### Keyboard Navigation Testing

```javascript
test("should be keyboard accessible", async () => {
  const user = userEvent.setup();
  render(<Component />);

  // Tab to element
  await user.tab();
  expect(screen.getByRole("button")).toHaveFocus();

  // Activate with Enter
  await user.keyboard("{Enter}");
  expect(mockHandler).toHaveBeenCalled();
});
```

#### Color Contrast Testing

```javascript
import { meetsContrastRequirement } from "../utils/accessibility";

test("should meet color contrast requirements", () => {
  expect(meetsContrastRequirement("#2563eb", "#ffffff")).toBe(true);
});
```

### Manual Testing

#### Screen Reader Testing

1. **NVDA (Windows)** - Free screen reader
2. **JAWS (Windows)** - Professional screen reader
3. **VoiceOver (macOS)** - Built-in screen reader
4. **Orca (Linux)** - Open source screen reader

**Testing Checklist:**

- [ ] All content is announced correctly
- [ ] Navigation landmarks work properly
- [ ] Form labels and errors are announced
- [ ] Dynamic content updates are announced
- [ ] Focus management works correctly

#### Keyboard Testing

**Testing Checklist:**

- [ ] All functionality available via keyboard
- [ ] Logical tab order
- [ ] Focus indicators visible
- [ ] No keyboard traps (except modals)
- [ ] Skip links work correctly

#### Color and Contrast Testing

**Tools:**

- WebAIM Contrast Checker
- Colour Contrast Analyser
- Browser DevTools accessibility panel

**Testing Checklist:**

- [ ] Text meets contrast requirements
- [ ] Focus indicators meet contrast requirements
- [ ] Information not conveyed by color alone
- [ ] High contrast mode works correctly

## Common Accessibility Issues and Solutions

### Issue: Missing Form Labels

```jsx
// ❌ Problem
<input type="email" placeholder="Email" />

// ✅ Solution
<label htmlFor="email">Email Address</label>
<input id="email" type="email" />
```

### Issue: Inaccessible Custom Components

```jsx
// ❌ Problem
<div onClick={handleClick}>Button</div>

// ✅ Solution
<button onClick={handleClick}>Button</button>
// or
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={handleKeyDown}
>
  Button
</div>
```

### Issue: Missing Error Announcements

```jsx
// ❌ Problem
{
  error && <div className="error">{error}</div>;
}

// ✅ Solution
{
  error && (
    <div role="alert" aria-live="assertive">
      {error}
    </div>
  );
}
```

### Issue: Poor Focus Management

```jsx
// ❌ Problem - Focus lost after action
const handleDelete = () => {
  deleteItem();
  // Focus is lost
};

// ✅ Solution - Manage focus appropriately
const handleDelete = () => {
  deleteItem();
  // Focus next item or return to list
  nextItemRef.current?.focus();
};
```

## Accessibility Testing Checklist

### Pre-Release Testing

- [ ] Run automated axe tests
- [ ] Test keyboard navigation
- [ ] Verify color contrast ratios
- [ ] Test with screen reader
- [ ] Check responsive design
- [ ] Verify reduced motion support
- [ ] Test high contrast mode
- [ ] Validate HTML semantics

### User Acceptance Testing

- [ ] Test complete user workflows
- [ ] Verify error handling accessibility
- [ ] Test form validation announcements
- [ ] Check loading state announcements
- [ ] Validate navigation announcements
- [ ] Test with real assistive technology users

## Resources and Tools

### Testing Tools

- **axe DevTools** - Browser extension for accessibility testing
- **WAVE** - Web accessibility evaluation tool
- **Lighthouse** - Built-in Chrome accessibility audit
- **Pa11y** - Command line accessibility testing
- **jest-axe** - Automated testing with Jest

### Documentation

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Resources](https://webaim.org/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)

### Screen Readers

- [NVDA](https://www.nvaccess.org/) - Free Windows screen reader
- [JAWS](https://www.freedomscientific.com/products/software/jaws/) - Professional Windows screen reader
- [VoiceOver](https://www.apple.com/accessibility/vision/) - Built-in macOS/iOS screen reader
- [Orca](https://wiki.gnome.org/Projects/Orca) - Linux screen reader

## Maintenance and Updates

### Regular Audits

- Run accessibility tests with each release
- Update color palette when design changes
- Review new components for accessibility
- Test with latest assistive technologies

### Team Training

- Provide accessibility training for developers
- Include accessibility in code review process
- Maintain accessibility documentation
- Share accessibility best practices

### User Feedback

- Provide accessible feedback mechanisms
- Respond to accessibility issues promptly
- Include users with disabilities in testing
- Continuously improve based on feedback

## Contact and Support

For accessibility questions or issues:

- Create an issue in the project repository
- Contact the development team
- Refer to this documentation for guidance
- Consult WCAG guidelines for specific requirements

Remember: Accessibility is not a one-time implementation but an ongoing commitment to inclusive design.
