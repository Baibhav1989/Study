"""Detailed HTML body content for each Order Management section."""

OM_SECTIONS: dict[str, str] = {}


def _s(section_id: str, html: str) -> None:
    OM_SECTIONS[section_id] = html.strip()


_s('om-overview', '''
      <h2>1. Industries Order Management Overview</h2>
      <p><strong>Salesforce Industries Order Management (IOM)</strong> is the fulfillment engine that runs after CPQ captures an order. While CPQ handles configure-price-quote, IOM answers: <em>what technical work must happen, in what order, through which systems, and when is the customer&apos;s service live?</em></p>

      <div class="tip"><strong>Simple analogy</strong> CPQ is placing your order at a restaurant. <strong>Decomposition</strong> is the kitchen ticket that breaks &quot;burger meal&quot; into grill, fries, and drink prep lines. <strong>Orchestration</strong> is the head chef coordinating stations, waiters, suppliers, and quality checks until the meal is delivered.</div>

      <h3>Two Primary Areas of IOM</h3>
      <table class="data-table">
        <thead><tr><th>Area</th><th>When It Runs</th><th>What It Does</th><th>Key Output</th></tr></thead>
        <tbody>
          <tr><td><strong>Order Decomposition</strong></td><td>After order is submitted; user clicks <strong>Decompose Order</strong></td><td>Maps commercial products to technical products (CFS, RFS, resources) using decomposition relationships in Product Console</td><td>Fulfillment Request Lines (FRLs) with Add, Modify, Disconnect, or NoChange actions</td></tr>
          <tr><td><strong>Order Orchestration</strong></td><td>After successful decomposition</td><td>Dynamically generates orchestration plans, sequences tasks, calls external systems, routes manual work to queues</td><td>Completed order, assets/inventory, provisioned services</td></tr>
        </tbody>
      </table>

      <h3>What You Will Learn (Exercise Guide)</h3>
      <p>Based on Spring &apos;22 Industries CME Cloud, the orchestration module teaches you to:</p>
      <ul>
        <li>Define design-time <strong>orchestration plan definitions</strong> (swimlanes) and <strong>item definitions</strong> (tasks)</li>
        <li>Generate runtime <strong>orchestration plans</strong> and <strong>orchestration items</strong> per order</li>
        <li>Trigger processing via <strong>orchestration scenarios</strong> (product + action)</li>
        <li>Sequence work with <strong>dependency definitions</strong> and <strong>scope</strong></li>
        <li>Integrate people (<strong>manual tasks/queues</strong>) and systems (<strong>callouts</strong>, <strong>auto tasks</strong>)</li>
        <li>Handle MACD change orders, cancellation, rollback, and fallout</li>
      </ul>

      <h3>Prerequisites</h3>
      <p>Solid Salesforce fundamentals, basic order-management concepts, and familiarity with telecom/media/energy business flows. Decomposition exercises (multi-level product relationships) should be completed before orchestration labs.</p>

      <h3>End-to-End Lifecycle</h3>
      <div class="workflow">
        <div class="workflow-step">CPQ Cart / Order</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Decompose Order</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">FRLs Created</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Scenarios Match</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Plans Generated</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Tasks Execute</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Assets &amp; Complete</div>
      </div>

      <h3>Exercise Map</h3>
      <table class="data-table">
        <thead><tr><th>Exercise</th><th>Topic</th><th>Time</th></tr></thead>
        <tbody>
          <tr><td>6-1</td><td>E2E Master Plan, milestones, DSL scenario</td><td>15 min</td></tr>
          <tr><td>6-2</td><td>Generate &amp; inspect first orchestration plan</td><td>15 min</td></tr>
          <tr><td>6-3</td><td>Credit Check manual task + queue</td><td>30 min</td></tr>
          <tr><td>6-4</td><td>Create Assets auto task (Assetizer)</td><td>15 min</td></tr>
          <tr><td>6-5</td><td>Dependency definitions (sequencing)</td><td>15 min</td></tr>
          <tr><td>6-6</td><td>Installation system callout</td><td>~45 min</td></tr>
          <tr><td>6-7</td><td>Fallout management &amp; retry policies</td><td>~60 min</td></tr>
          <tr><td>6-8</td><td>Push events (JSON &amp; Apex)</td><td>~30 min</td></tr>
          <tr><td>6-9 – 6-11</td><td>MACD 1:1, Disconnect, 1:M (Spotify / Streaming TV)</td><td>60+ min each</td></tr>
          <tr><td>6-12 – 6-14</td><td>Cancellation, rollback groups, advanced challenge</td><td>60+ min</td></tr>
        </tbody>
      </table>
''')

_s('om-decomp', '''
      <h2>2. Order Decomposition — Concepts &amp; Configuration</h2>
      <p><strong>Decomposition</strong> is the bridge between what the customer ordered (commercial catalog) and what fulfillment systems must execute (technical catalog). Until decomposition succeeds, orchestration does not start.</p>

      <h3>Core Concepts</h3>
      <table class="data-table">
        <thead><tr><th>Term</th><th>Meaning</th></tr></thead>
        <tbody>
          <tr><td><strong>Commercial product</strong></td><td>What sales/CPQ sells (e.g. Spotify Offer, DSL Service)</td></tr>
          <tr><td><strong>Technical product</strong></td><td>CFS, RFS, or Resource that provisioning/billing systems understand</td></tr>
          <tr><td><strong>FRL</strong></td><td>Fulfillment Request Line — one decomposed line with an action (Add/Modify/Disconnect/NoChange)</td></tr>
          <tr><td><strong>Mappings Data</strong></td><td>Attribute mappings from commercial → technical in decomposition relationship</td></tr>
          <tr><td><strong>Inventory Item JSON</strong></td><td>Technical inventory stored after assetization; used for MACD comparisons</td></tr>
        </tbody>
      </table>

      <h3>What Happens When You Click Decompose Order</h3>
      <ol>
        <li>IOM reads decomposition relationships from Product Console for each order line</li>
        <li>Commercial attributes map to technical attributes (often ad-verbatim or via rules)</li>
        <li>FRLs are created on the decomposed order view — one row per technical product + action</li>
        <li>For <strong>new orders</strong>, actions are typically <strong>Add</strong></li>
        <li>For <strong>MACD</strong>, IOM compares existing inventory (&quot;as-is&quot;) vs requested state (&quot;as-requested&quot;) and may emit multiple FRLs (e.g. Disconnect + Add on upgrade)</li>
        <li>Each FRL becomes input to orchestration scenarios (product on FRL + action)</li>
      </ol>

      <h3>Decomposition Models</h3>
      <table class="data-table">
        <thead><tr><th>Model</th><th>Structure</th><th>When to Use</th><th>Lab Example</th></tr></thead>
        <tbody>
          <tr><td><strong>1:1</strong></td><td>One commercial → one technical</td><td>Simple single-service rollout</td><td>Spotify → Spotify RFS</td></tr>
          <tr><td><strong>Many-to-one</strong></td><td>Multiple commercial offers → shared technical RFS</td><td>Future product tiers sharing one fulfillment path</td><td>Multiple music tiers → one RFS</td></tr>
          <tr><td><strong>Multi-level (CFS/RFS)</strong></td><td>Commercial → CFS → RFS abstraction layers</td><td>TM Forum / SID style; catalog likely to expand</td><td>DSL Service → VDSL2 CFS → underlying RFS</td></tr>
          <tr><td><strong>1:M</strong></td><td>One commercial → many technical FRLs</td><td>Shipping + activation, multiple resources per offer</td><td>Streaming TV → ship STB + activation RFS</td></tr>
        </tbody>
      </table>

      <h3>How to Configure Decomposition (Step-by-Step)</h3>
      <div class="example-box">
        <strong>Exercise 6-9 — Spotify 1:1 Configuration</strong>
        <ol>
          <li><strong>Product Console</strong> → open commercial product <em>Spotify</em></li>
          <li>Review <strong>General Properties</strong> and <strong>Attributes and Fields</strong>: Number of Accounts, Spotify Subscription Type, Install Account Name</li>
          <li>Open technical product <em>Spotify RFS</em> — review matching technical attributes</li>
          <li><strong>Products</strong> tab → open decomposition relationship Spotify → Spotify RFS</li>
          <li>Configure <strong>Mappings Data</strong> — map commercial attributes through; condition rules optional in lab</li>
          <li>Place order → cart → <strong>Decompose Order</strong></li>
          <li>Verify FRL: Spotify (commercial) decomposed to Spotify RFS with <strong>Add</strong> action; attributes mapped ad-verbatim</li>
          <li>After orchestration assetization completes, click FRL hyperlink to view <strong>technical inventory JSON</strong></li>
        </ol>
      </div>

      <h3>MACD Decomposition Logic</h3>
      <p>On change orders, IOM builds an in-memory decision tree:</p>
      <ul>
        <li>Loads <strong>as-is</strong> state from Inventory Item JSON on existing assets</li>
        <li>Compares to <strong>as-requested</strong> decomposition from the change order</li>
        <li>Generates FRLs: e.g. <strong>Disconnect</strong> Bronze TV + <strong>Add</strong> Silver TV when upgrading tier</li>
        <li>Each FRL triggers its own orchestration scenarios and swimlanes</li>
      </ul>

      <div class="warning"><strong>Design tip (from PDF)</strong> MACD requires end-to-end thinking, but prioritize <em>downstream system capabilities</em> first and work backward — provisioning, billing, logistics, and assetization constraints drive both decomposition and orchestration design.</div>

      <h3>Verifying Decomposition</h3>
      <table class="data-table">
        <thead><tr><th>Check</th><th>Where to Look</th></tr></thead>
        <tbody>
          <tr><td>Source commercial line</td><td>Link icon on decomposition page for OLI</td></tr>
          <tr><td>Destination FRL</td><td>Link icon on technical fulfillment request</td></tr>
          <tr><td>Action type</td><td>Add / Modify / Disconnect on each FRL row</td></tr>
          <tr><td>Asset appeared</td><td>Refresh after assetization — inventory only exists after Create Assets completes</td></tr>
        </tbody>
      </table>
''')

_s('om-decomp-orch', '''
      <h2>3. Decomposition vs Orchestration</h2>
      <p>These are sequential phases — not alternatives. Decomposition answers <em>what</em> must be fulfilled; orchestration answers <em>how and in what order</em>.</p>

      <div class="workflow">
        <div class="workflow-step">CPQ Order Submitted</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Decompose Order</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">FRLs on Decomposed Order</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">View Orchestration Plan</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Swimlanes Execute</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Order Complete</div>
      </div>

      <h3>Side-by-Side Comparison</h3>
      <table class="data-table">
        <thead><tr><th></th><th>Decomposition</th><th>Orchestration</th></tr></thead>
        <tbody>
          <tr><td><strong>Configured in</strong></td><td>Product Console (decomposition relationships)</td><td>Orchestration Plan Definitions, Items, Scenarios, Dependencies</td></tr>
          <tr><td><strong>Runtime objects</strong></td><td>FRLs, decomposed order view</td><td>Orchestration plans, orchestration items, queues</td></tr>
          <tr><td><strong>Triggered by</strong></td><td>Decompose Order button</td><td>Automatic after decomposition + scenario match</td></tr>
          <tr><td><strong>Human interaction</strong></td><td>Usually none (batch transform)</td><td>Manual tasks, fallout repair, monitoring plan UI</td></tr>
          <tr><td><strong>External systems</strong></td><td>No direct calls</td><td>Callouts, push events, auto tasks</td></tr>
        </tbody>
      </table>

      <h3>The Orchestration Execution Engine</h3>
      <p>Once decomposition completes, the engine:</p>
      <ul>
        <li>Evaluates each FRL against <strong>orchestration scenarios</strong> (product + action)</li>
        <li>Instantiates matching <strong>orchestration plan definitions</strong> as runtime plans (swimlanes)</li>
        <li>Creates <strong>orchestration items</strong> from item definitions</li>
        <li>Resolves <strong>dependencies</strong> and <strong>conditions</strong> — items move Pending → Ready → Running → Completed</li>
        <li>Coordinates parallel swimlanes while respecting cross-lane dependencies</li>
      </ul>

      <div class="note"><strong>Key insight</strong> One order typically generates <em>multiple</em> swimlanes in parallel (E2E, Provision, Billing, etc.). Dependencies tie them together — e.g. assetization waits for billing and provisioning.</div>
''')

_s('om-plan-def', '''
      <h2>4. Swimlanes &amp; Orchestration Plan Definitions</h2>
      <p>An <strong>orchestration plan definition</strong> is the design-time template for a <strong>swimlane</strong> — a horizontal row on the Orchestration Plan page containing related tasks.</p>

      <h3>Plan Definition Anatomy</h3>
      <table class="data-table">
        <thead><tr><th>Component</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td><strong>Plan Definition</strong></td><td>Named container = one swimlane (e.g. E2E Master Plan, Spotify Billing)</td></tr>
          <tr><td><strong>Item Definitions</strong></td><td>Tasks inside the plan (milestones, manual, callout, auto, push) — cannot be shared across plans</td></tr>
          <tr><td><strong>Scenarios</strong></td><td>Rules: when this plan runs (Product + Action on FRL)</td></tr>
          <tr><td><strong>Show Order</strong></td><td>Integer controlling vertical position on plan UI (1 = top)</td></tr>
          <tr><td><strong>Scope</strong></td><td>Default dependency resolution boundary for items in this plan (usually Global)</td></tr>
        </tbody>
      </table>

      <h3>Exercise 6-1 — Create E2E Master Plan</h3>
      <table class="data-table">
        <thead><tr><th>Step</th><th>Action</th><th>Values</th></tr></thead>
        <tbody>
          <tr><td>1</td><td>App Launcher → <strong>Orchestration Plan Definitions</strong> → New</td><td>Name: <em>E2E Master Plan</em>, Show Order: <em>1</em></td></tr>
          <tr><td>2</td><td>Item Definitions → New → Milestone</td><td><em>Start Order</em>, Scope: Global</td></tr>
          <tr><td>3</td><td>Save &amp; New → Milestone</td><td><em>Complete Order</em>, Scope: Global</td></tr>
          <tr><td>4</td><td>Scenarios → New</td><td>DSL Service Scenario, Product: DSL Service, Action: Add</td></tr>
        </tbody>
      </table>

      <h3>Understanding Swimlanes</h3>
      <p>Think of each swimlane as a functional pipeline:</p>
      <ul>
        <li><strong>E2E swimlane</strong> — bookends the order (Start / Complete milestones) and cross-cutting tasks (Credit Check, Create Assets)</li>
        <li><strong>Provisioning swimlane</strong> — callouts to network/OSS systems</li>
        <li><strong>Billing swimlane</strong> — activate billing accounts/rates</li>
        <li><strong>Assetization swimlane</strong> — create customer assets / inventory</li>
        <li><strong>SMS / notification swimlanes</strong> — welcome or upgrade messages per MACD action</li>
      </ul>

      <h3>Exercise 6-9 — Spotify MACD Swimlanes</h3>
      <table class="data-table">
        <thead><tr><th>Plan Definition</th><th>Show Order</th><th>Tasks (lab)</th><th>Scenario Product / Action</th></tr></thead>
        <tbody>
          <tr><td>Spotify E2E</td><td>1</td><td>Spotify Start, Spotify End milestones</td><td>Spotify RFS — Add, Modify</td></tr>
          <tr><td>Spotify Provision</td><td>2</td><td>Spotify Provision milestone (callout in prod)</td><td>Spotify RFS — Add, Modify</td></tr>
          <tr><td>Spotify Billing</td><td>3</td><td>Billing milestone</td><td>Spotify RFS — Add, Modify</td></tr>
          <tr><td>Spotify Assetize</td><td>4</td><td>Auto task (Assetize)</td><td>Spotify RFS — Add, Modify</td></tr>
          <tr><td>Spotify SMS Welcome</td><td>5</td><td>Welcome SMS milestone</td><td>Spotify RFS — Add only</td></tr>
          <tr><td>Spotify SMS Upgrade</td><td>6</td><td>Upgrade SMS milestone</td><td>Spotify RFS — Modify only</td></tr>
        </tbody>
      </table>

      <h3>Industry Best Practices</h3>
      <ul>
        <li>One main E2E plan sequences major milestones for <em>all</em> orders (Start → Complete)</li>
        <li>Separate plan per macro function: provisioning, logistics, inventory, billing</li>
        <li>Keep plans simple — avoid loops unless absolutely required</li>
        <li>Assetization auto task should be <strong>second-to-last</strong>, immediately before Complete Order</li>
        <li>Plan definitions are <strong>reusable</strong> — associate multiple products via scenarios</li>
        <li>Create all plan + item definitions first, <em>then</em> dependencies (recommended order)</li>
      </ul>

      <div class="tip"><strong>Prototyping tip</strong> Use Milestone tasks for everything except assetization during design/test — convert to callouts and manual tasks before production.</div>
''')

_s('om-generate', '''
      <h2>5. Generating Orchestration Plans (Exercise 6-2)</h2>
      <p>Design-time configuration becomes a living workflow when you decompose an order and click <strong>View Orchestration Plan</strong>. The execution engine creates runtime records: orchestration plan instances, orchestration items, dependency links, and queue assignments.</p>

      <h3>Full Test Procedure</h3>
      <ol>
        <li><strong>Orders</strong> → New → Name: <em>E2E Master Plan Test Order</em>, Account: White Noah, B2C Price List</li>
        <li><strong>Configure Order</strong> (Power Launcher) → add <em>DSL Service</em> to cart</li>
        <li>Configure Download Speed = 40 Mbps → Close cart</li>
        <li>Click <strong>Decompose Order</strong> — verify multi-level decomposition (DSL Service → VDSL2 CFS → …)</li>
        <li>Click <strong>View Orchestration Plan</strong> — orchestration begins</li>
      </ol>

      <h3>Reading the Orchestration Plan UI</h3>
      <table class="data-table">
        <thead><tr><th>UI Element</th><th>Meaning</th></tr></thead>
        <tbody>
          <tr><td>Process box</td><td>One orchestration item (runtime task instance)</td></tr>
          <tr><td>Green box</td><td>Completed (milestones auto-complete when Ready)</td></tr>
          <tr><td>Blue box</td><td>Ready — waiting for agent/system or about to run</td></tr>
          <tr><td>Grey box</td><td>Pending — dependencies not yet satisfied</td></tr>
          <tr><td>Vertical layout without connectors</td><td>Tasks running in parallel (no dependencies yet)</td></tr>
          <tr><td>Connected segments</td><td>Dependency chain — sequential execution</td></tr>
          <tr><td>Mouse scroll</td><td>Zoom plan display</td></tr>
          <tr><td>Click + drag</td><td>Pan around large plans</td></tr>
        </tbody>
      </table>

      <h3>Debugging Runtime Items</h3>
      <ol>
        <li>Hover a process box → pop-up shows item details (Classic Cards layout)</li>
        <li>Right-click → <strong>View Record</strong> → Orchestration Item page (plan instance, state, queue)</li>
        <li>Order Item link → which product/scenario created this item</li>
        <li>Order/Fulfilment Request link → source order or FRL being processed</li>
      </ol>

      <div class="note"><strong>Behind the scenes</strong> First plan generation creates a web of interconnected records. Understanding this complexity matters when changing definitions on in-flight orders.</div>
''')

_s('om-item-types', '''
      <h2>6. Orchestration Item Types</h2>
      <p>Each <strong>orchestration item definition</strong> has a record type that determines what happens when the item reaches <strong>Ready</strong> state. Items also support <strong>conditions</strong> (attribute/field rules) and <strong>dependencies</strong> (sequencing).</p>

      <table class="data-table">
        <thead><tr><th>Type</th><th>What Happens at Ready</th><th>Fails?</th><th>Configuration Highlights</th><th>Lab Example</th></tr></thead>
        <tbody>
          <tr><td><span class="tag tag-green">Milestone</span></td><td>Marks stage; immediately completes</td><td>Never</td><td>Name, Scope; used for Start/Complete bookends</td><td>Start Order, Spotify Start</td></tr>
          <tr><td><span class="tag tag-blue">Manual Task</span></td><td>Appears in manual queue; user completes via URL/OmniScript</td><td>Yes</td><td>Manual Queue, Custom Task Execution URL (/apex/…)</td><td>Credit Check</td></tr>
          <tr><td><span class="tag tag-orange">Callout</span></td><td>REST/SOAP call via orchestration system interface</td><td>Yes</td><td>System, Interface, Path, retry/fallout settings</td><td>Schedule Installation</td></tr>
          <tr><td><span class="tag tag-purple">Auto Task</span></td><td>Invokes Apex via Item Implementation</td><td>Yes</td><td>Item Implementation (e.g. Assetize → XOMAutoTaskAssetizer)</td><td>Create Assets</td></tr>
          <tr><td><span class="tag tag-blue">Push Event</span></td><td>Waits for sObject state change (JSON or Apex trigger)</td><td>Yes</td><td>Object, field, expected value configuration</td><td>Exercise 6-8 tests</td></tr>
        </tbody>
      </table>

      <h3>Item State Machine</h3>
      <div class="state-flow">
        <span class="state-box">Pending</span><span class="state-arrow">→</span>
        <span class="state-box">Ready</span><span class="state-arrow">→</span>
        <span class="state-box">Running</span><span class="state-arrow">→</span>
        <span class="state-box">Completed</span>
      </div>
      <p>Failure paths: <strong>Failed</strong> (may retry/repair) or <strong>Fatally Failed</strong> (requires intervention). Milestones skip failure states entirely.</p>

      <h3>When Is an Item Ready?</h3>
      <p>An item becomes Ready only when <em>all</em> of the following are satisfied:</p>
      <ul>
        <li>All <strong>dependency definitions</strong> — predecessor items Completed</li>
        <li>All <strong>conditions</strong> — product/order attribute rules pass (if configured)</li>
        <li>Parent plan/scenario has been activated for this order</li>
      </ul>

      <h3>Advanced Item Fields (Later Labs)</h3>
      <ul>
        <li><strong>Point of No Return (PONR)</strong> — after completion, order cannot be cancelled</li>
        <li><strong>Rollback Plan Definition</strong> — plan to run on in-flight cancel</li>
        <li><strong>Rollback Group</strong> — groups items reversed together on cancel</li>
      </ul>
''')

_s('om-scenarios', '''
      <h2>7. Orchestration Scenarios</h2>
      <p><strong>Scenarios</strong> are the <em>trigger</em> that tells IOM: &quot;for this FRL (product + action), execute this plan definition.&quot; Without a matching scenario, a swimlane is not generated.</p>

      <h3>Scenario Fields</h3>
      <table class="data-table">
        <thead><tr><th>Field</th><th>Purpose</th><th>Example</th></tr></thead>
        <tbody>
          <tr><td><strong>Name</strong></td><td>Administrative label</td><td>DSL Service Scenario</td></tr>
          <tr><td><strong>Product</strong></td><td>Technical product on the FRL (not always commercial)</td><td>DSL Service, Spotify RFS, Installation System Resource</td></tr>
          <tr><td><strong>Action</strong></td><td>Add, Modify, Disconnect, NoChange (multi-select in MACD labs)</td><td>Add only for new install; Add+Modify for Spotify provision</td></tr>
          <tr><td><strong>Conditions</strong> (optional)</td><td>Further filter by attributes</td><td>Ship STB Silver when tier=Silver AND region=SoCal</td></tr>
        </tbody>
      </table>

      <h3>How Scenarios Drive Multi-Swimlane Plans</h3>
      <p>One decomposed order with multiple FRLs can spawn many swimlanes simultaneously:</p>
      <ul>
        <li>FRL: DSL Service + Add → E2E Master Plan scenario fires</li>
        <li>FRL: Installation System Resource + Add → Installation System swimlane fires</li>
        <li>FRL: Spotify RFS + Modify → Provision, Billing, Assetize, SMS Upgrade lanes fire</li>
      </ul>

      <div class="example-box">
        <strong>E2E vs functional scenarios</strong>
        <ul>
          <li><strong>Spotify E2E scenario</strong> — Product: Spotify RFS, Actions: Add + Modify — only milestones, frames the order</li>
          <li><strong>Spotify SMS Welcome</strong> — same product, Action: <em>Add only</em> — welcome message on new subscription</li>
          <li><strong>Spotify SMS Upgrade</strong> — Action: <em>Modify only</em> — different message on plan change</li>
        </ul>
      </div>

      <div class="warning"><strong>Modify trap (Exercise 6-11)</strong> For Streaming TV, a Modify on service tier may <em>not</em> need a dedicated modify swimlane — decomposition emits Disconnect + Add FRLs instead, each triggering add/disconnect scenarios.</div>
''')

_s('om-dependencies', '''
      <h2>8. Orchestration Dependency Definitions (Exercise 6-5)</h2>
      <p>Without dependencies, all items in a plan start in parallel — a critical bug in the E2E lab where <strong>Create Assets could run before Credit Check passes</strong>. Dependencies enforce business-logic sequencing within and across swimlanes.</p>

      <h3>Dependency Concepts</h3>
      <table class="data-table">
        <thead><tr><th>Concept</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td><strong>Dependency Definition</strong></td><td>Link on item A: &quot;A depends on B completing first&quot;</td></tr>
          <tr><td><strong>Dependency Item Definition</strong></td><td>The predecessor task that must reach Completed</td></tr>
          <tr><td><strong>Depends On / Should Be Processed Before</strong></td><td>Same logic — forward vs backward naming only</td></tr>
          <tr><td><strong>Scope</strong></td><td>Global, Swimlane, etc. — how engine resolves cross-plan dependencies</td></tr>
        </tbody>
      </table>

      <h3>E2E Master Plan — Required Sequence</h3>
      <div class="workflow">
        <div class="workflow-step">Start Order</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Credit Check</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Create Assets</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Complete Order</div>
      </div>

      <h3>Configuration Steps</h3>
      <table class="data-table">
        <thead><tr><th>On Item</th><th>Depends On</th><th>Scope</th></tr></thead>
        <tbody>
          <tr><td>Credit Check</td><td>Start Order</td><td>Global</td></tr>
          <tr><td>Create Assets</td><td>Credit Check</td><td>Global</td></tr>
          <tr><td>Complete Order</td><td>Create Assets</td><td>Global</td></tr>
        </tbody>
      </table>
      <ol>
        <li>Open E2E Master Plan → click item (e.g. Credit Check) → <strong>Related</strong> tab</li>
        <li>Orchestration Dependency Definitions → <strong>New</strong></li>
        <li>Select Dependency Item Definition, set Scope, Save</li>
        <li>Repeat for each dependent item</li>
      </ol>

      <h3>Cross-Swimlane Dependencies (MACD Labs)</h3>
      <p>Dependencies commonly link E2E milestones to functional lanes:</p>
      <ul>
        <li>Spotify Provision depends on Spotify Start (E2E)</li>
        <li>Spotify Assetize depends on Spotify Billing + Spotify Provision</li>
        <li>Spotify End depends on all functional lanes completing</li>
      </ul>

      <h3>Testing Dependencies</h3>
      <ol>
        <li>Clone a prior test order → increment name → set Status Draft → Save</li>
        <li>Configure cart → Decompose → View Orchestration Plan</li>
        <li>Credit Check shows <strong>blue (Ready)</strong>; Create Assets and Complete Order <strong>grey (Pending)</strong></li>
        <li>Complete Credit Check manually → Create Assets becomes Ready → then Complete Order</li>
      </ol>

      <div class="tip"><strong>Best practice</strong> Use the same Dependency Type throughout a plan — mixing types causes confusion even though functionally equivalent.</div>
''')

_s('om-manual', '''
      <h2>9. Manual Tasks &amp; Manual Queues (Exercise 6-3)</h2>
      <p>Some fulfillment steps require human judgment — credit approval, engineering review, fraud checks. <strong>Manual tasks</strong> pause orchestration until an agent completes work in a <strong>manual queue</strong>.</p>

      <h3>Manual Task vs Manual Queue</h3>
      <table class="data-table">
        <thead><tr><th>Object</th><th>Who Creates</th><th>Purpose</th></tr></thead>
        <tbody>
          <tr><td><strong>Manual Queue</strong></td><td>Administrator</td><td>Team inbox — agents pick tasks (e.g. Credit Check queue)</td></tr>
          <tr><td><strong>Manual Task</strong></td><td>On plan definition</td><td>Orchestration item that routes work to a queue + launch URL</td></tr>
          <tr><td><strong>Orchestration Queue</strong></td><td>Managed package</td><td>Internal engine queue — different from manual queue</td></tr>
        </tbody>
      </table>

      <h3>Credit Check — Full Configuration</h3>
      <h4>Step 1: Create Manual Queue</h4>
      <ol>
        <li><strong>Manual Queues</strong> tab → New</li>
        <li>Manual Queue: <em>Credit Check</em>, Queue Type: <em>None</em> → Save</li>
      </ol>

      <h4>Step 2: Get OmniScript Launch URL</h4>
      <ol>
        <li>Open prebuilt <em>VU/Credit Check</em> OmniScript → review Perform Credit Check steps</li>
        <li>Click <strong>How to launch activated script</strong></li>
        <li>Page type: Universal Page with Header/Sidebar</li>
        <li>Copy relative URL starting with <code>/apex/...</code> (no domain)</li>
      </ol>

      <h4>Step 3: Create Manual Task Item</h4>
      <table class="data-table">
        <thead><tr><th>Field</th><th>Value</th></tr></thead>
        <tbody>
          <tr><td>Record Type</td><td>Manual Task</td></tr>
          <tr><td>Name</td><td>Credit Check</td></tr>
          <tr><td>Scope</td><td>Global</td></tr>
          <tr><td>Manual Queue</td><td>Credit Check</td></tr>
          <tr><td>Custom Task Execution URL</td><td>Pasted /apex/… URL</td></tr>
        </tbody>
      </table>

      <h3>Runtime Flow</h3>
      <ol>
        <li>Order decomposed → plan generated → Credit Check turns Ready (blue)</li>
        <li>Agent opens Manual Queue → launches Credit Check OmniScript</li>
        <li>Agent completes script → marks task complete</li>
        <li>Engine advances — Create Assets becomes Ready</li>
      </ol>

      <h3>Auto-Assignment (Tasks 4–5)</h3>
      <p>Configure rules to automatically assign Salesforce users to manual tasks based on skills, territories, or round-robin — reduces queue pickup latency in production contact centers.</p>

      <div class="warning"><strong>URL alert</strong> Custom Task Execution URL must be relative (<code>/apex/...</code>). Absolute URLs break OmniScript launch from orchestration context.</div>
''')

_s('om-auto', '''
      <h2>10. Auto Tasks — Create Assets (Exercise 6-4)</h2>
      <p><strong>Auto tasks</strong> run Apex automatically when Ready — no human queue. The most common pattern is <strong>assetization</strong>: converting fulfilled order lines into durable customer assets and inventory records.</p>

      <h3>Auto Task vs Manual Task</h3>
      <table class="data-table">
        <thead><tr><th></th><th>Auto Task</th><th>Manual Task</th></tr></thead>
        <tbody>
          <tr><td>Execution</td><td>Automatic via Item Implementation</td><td>Agent-driven via queue + URL</td></tr>
          <tr><td>Apex</td><td>XOMAutoTaskAssetizer or custom class</td><td>Usually OmniScript UI</td></tr>
          <tr><td>Typical position</td><td>Second-to-last before Complete Order</td><td>Mid-flow approvals</td></tr>
        </tbody>
      </table>

      <h3>Assetizer Implementation</h3>
      <ul>
        <li>Search <strong>Item Implementations</strong> → <em>Assetize</em></li>
        <li>Apex class: <code>XOMAutoTaskAssetizer</code> (managed package)</li>
        <li>Creates assets from order — enables MACD, inventory comparisons, and customer service views</li>
        <li>Customers can author custom item implementations for specialized Apex logic</li>
      </ul>

      <h3>Create Assets Configuration</h3>
      <table class="data-table">
        <thead><tr><th>Field</th><th>Value</th></tr></thead>
        <tbody>
          <tr><td>Plan</td><td>E2E Master Plan</td></tr>
          <tr><td>Record Type</td><td>Auto Task</td></tr>
          <tr><td>Name</td><td>Create Assets</td></tr>
          <tr><td>Scope</td><td>Global</td></tr>
          <tr><td>Item Implementation</td><td>Assetize</td></tr>
        </tbody>
      </table>

      <h3>Testing</h3>
      <ol>
        <li>Clone test order #2 → increment number → Draft → Save</li>
        <li>Configure DSL Service → Decompose → View Orchestration Plan</li>
        <li>Credit Check blue (Ready) — complete it first if dependencies configured</li>
        <li>Create Assets runs automatically → turns green (Completed)</li>
        <li>Return to decomposed order — inventory/asset JSON now visible on FRL hyperlink</li>
      </ol>

      <div class="tip"><strong>Timing note</strong> Create Assets may briefly show blue before green — refresh if state seems stuck. Display order of parallel tasks may vary.</div>
''')

_s('om-callouts', '''
      <h2>11. Orchestration Systems &amp; Callouts (Exercise 6-6)</h2>
      <p><strong>Callouts</strong> automate integration with external fulfillment systems (OSS, billing, logistics, installation schedulers) via REST/SOAP through configured <strong>orchestration systems</strong> and <strong>system interfaces</strong>.</p>

      <h3>Architecture</h3>
      <table class="data-table">
        <thead><tr><th>Layer</th><th>Object</th><th>Role</th></tr></thead>
        <tbody>
          <tr><td>System</td><td>Orchestration System</td><td>Logical external system (Training Mocker, Billing Gateway)</td></tr>
          <tr><td>Interface</td><td>System Interface</td><td>Endpoint URL, credentials, paths, HTTP method</td></tr>
          <tr><td>Task</td><td>Callout Item Definition</td><td>Which interface/path to invoke when Ready</td></tr>
          <tr><td>Trigger</td><td>Scenario</td><td>Product + Action that activates the plan containing callout</td></tr>
        </tbody>
      </table>

      <h3>Installation System Lab — Full Steps</h3>
      <ol>
        <li>Review installation system orchestration diagram (logical view)</li>
        <li>Create orchestration system: <strong>Training Mocker</strong></li>
        <li>Create <strong>system interface</strong> with endpoint URL and path</li>
        <li>Add <strong>Remote Site Settings</strong> for external URL in Salesforce Setup</li>
        <li>Set technical product <em>Installation System Resource</em> scope to Default</li>
        <li>Create <strong>Installation System</strong> plan definition + <em>Schedule Installation</em> callout item</li>
        <li>Create scenario: Product = Installation System Resource, Action = Add</li>
        <li>Test order: Back to School Student Offer + DSL 40 Mbps + Home Hub Modem Best grade</li>
        <li>Decompose → verify OLI decomposes to Installation System Resource FRL with Add</li>
        <li>View Orchestration Plan — E2E + Installation swimlanes; Schedule Installation in Installation lane</li>
      </ol>

      <h3>Attribute-Driven Behavior (Task 10)</h3>
      <p>Changing product attributes (e.g. Download Speed on DSL) can change which callout paths or conditions fire — always regression-test attribute combinations after orchestration changes.</p>

      <h3>Callout Failure</h3>
      <p>Failed callouts move to Failed state — may trigger retry policies and fallout queues (Exercise 6-7). System interfaces can be taken offline to simulate outages.</p>
''')

_s('om-fallout', '''
      <h2>12. Fallout Management &amp; Retry Policies (Exercise 6-7)</h2>
      <p>Production integrations fail — networks timeout, endpoints return 500, DNS breaks. <strong>Integration Retry Policies</strong> and <strong>fallout management</strong> provide automated recovery and human repair paths.</p>

      <h3>Key Concepts</h3>
      <table class="data-table">
        <thead><tr><th>Feature</th><th>Purpose</th></tr></thead>
        <tbody>
          <tr><td><strong>Integration Retry Policy</strong></td><td>Automatic retries with configurable intervals/counts</td></tr>
          <tr><td><strong>Fallout Queue</strong></td><td>Manual queue for tasks that exhausted retries</td></tr>
          <tr><td><strong>Repair</strong></td><td>Agent fixes root cause (config, data) and retries/resumes item</td></tr>
          <tr><td><strong>System Interface offline</strong></td><td>Simulates hard outage — tests fallout routing</td></tr>
        </tbody>
      </table>

      <h3>Lab Progression</h3>
      <ol>
        <li><strong>Task 1–2:</strong> Confirm org supports retry policies; misconfigure Path → observe retry behavior</li>
        <li><strong>Task 3:</strong> Misconfigure System URL → stronger failure signal</li>
        <li><strong>Task 4:</strong> Additional fallout configuration (queues, notifications)</li>
        <li><strong>Task 5:</strong> Test retry policies with fallout queues — failed callout lands in repair queue</li>
        <li><strong>Task 6:</strong> Repair IOM config, fix DNS (MAC vs PC hosts file notes in PDF)</li>
        <li><strong>Task 7:</strong> Take system interface offline — verify graceful degradation</li>
      </ol>

      <div class="note"><strong>Operations reality</strong> Fallout queues are your NOC/operations dashboard for stuck orders. Design clear ownership per queue aligned to integration domain (billing, network, logistics).</div>
''')

_s('om-push', '''
      <h2>13. Push Events (Exercise 6-8)</h2>
      <p>Not all fulfillment is request/response. <strong>Push events</strong> let orchestration items wait for asynchronous signals — an external system or Salesforce object state change confirms work is done.</p>

      <h3>When to Use Push Events</h3>
      <ul>
        <li>External system completes work asynchronously and updates a Salesforce field</li>
        <li>Downstream team marks a custom object stage complete</li>
        <li>Event-driven architecture where polling callouts are undesirable</li>
      </ul>

      <h3>Lab Structure</h3>
      <ol>
        <li>Create orchestration plan definition with push event item definitions</li>
        <li>Place test order → decompose → observe item waiting in Running/Ready for push</li>
        <li><strong>Task 4 — JSON push:</strong> Configure JSON-based push event; simulate object update</li>
        <li><strong>Task 5 — Apex push:</strong> Apex trigger/class fires push to advance orchestration</li>
      </ol>

      <h3>Push vs Callout</h3>
      <table class="data-table">
        <thead><tr><th></th><th>Callout</th><th>Push Event</th></tr></thead>
        <tbody>
          <tr><td>Pattern</td><td>Active request → immediate response expected</td><td>Fire-and-forget → wait for signal</td></tr>
          <tr><td>Completion</td><td>HTTP response success</td><td>Object state matches configured criteria</td></tr>
          <tr><td>Timeout handling</td><td>Retry/fallout on HTTP failure</td><td>May need timeout items or monitoring</td></tr>
        </tbody>
      </table>
''')

_s('om-macd-1to1', '''
      <h2>14. MACD with 1:1 Decomposition (Exercise 6-9)</h2>
      <p><strong>MACD</strong> = Move, Add, Change (Modify), Disconnect — the four order actions on existing customer services. With <strong>1:1 decomposition</strong>, one commercial product maps to one technical RFS, simplifying orchestration for Spotify&apos;s initial launch.</p>

      <h3>Logical Orchestration View (Add &amp; Modify)</h3>
      <p>The PDF diagrams show parallel functional swimlanes triggered by scenarios:</p>
      <ul>
        <li><strong>Add:</strong> E2E Start → Provision → Billing → Assetize → SMS Welcome → E2E End</li>
        <li><strong>Modify:</strong> Same core lanes but SMS Upgrade replaces Welcome; provision/billing may re-execute</li>
      </ul>

      <h3>Configuration Checklist (Tasks 3–10)</h3>
      <table class="data-table">
        <thead><tr><th>Task</th><th>Work</th></tr></thead>
        <tbody>
          <tr><td>3</td><td>Create 6 plan definitions (Spotify E2E, Provision, Billing, Assetize, SMS Welcome, SMS Upgrade) — Show Order 1–6, Scope Global</td></tr>
          <tr><td>4</td><td>E2E lane: Spotify Start + Spotify End milestones; scenarios for Add + Modify</td></tr>
          <tr><td>5</td><td>Provision lane: milestone + scenario (Spotify RFS, Add+Modify)</td></tr>
          <tr><td>6</td><td>Billing lane: milestone + scenario</td></tr>
          <tr><td>7</td><td>Assetize lane: Auto Task (Assetize) + scenario</td></tr>
          <tr><td>8</td><td>SMS Welcome: Add action only</td></tr>
          <tr><td>9</td><td>SMS Upgrade: Modify action only</td></tr>
          <tr><td>10</td><td>Cross-swimlane dependency definitions linking Start → functions → End</td></tr>
        </tbody>
      </table>

      <h3>Testing Add Order (Task 11)</h3>
      <ol>
        <li>Create new account + order with Spotify commercial product</li>
        <li>Configure attributes (Subscription Type, Number of Accounts)</li>
        <li>Decompose — verify Spotify → Spotify RFS Add FRL</li>
        <li><strong>View Orchestration Plan</strong> — all six swimlanes visible with tasks sequencing via dependencies</li>
        <li>Wait for assetization — refresh decomposition page — inventory JSON on FRL link</li>
      </ol>

      <h3>Testing Change Order (Task 12)</h3>
      <ol>
        <li>Submit MACD change on existing Spotify subscription (e.g. change subscription type)</li>
        <li>Decompose — Modify action on Spotify RFS</li>
        <li>Orchestration runs modify scenarios — SMS Upgrade lane fires instead of Welcome</li>
      </ol>

      <div class="tip"><strong>Naming convention</strong> Use noun+verb task names (Create Account, Activate Billing) rather than system names — simplifies migrations when backend systems change.</div>
''')

_s('om-macd-disconnect', '''
      <h2>15. MACD Disconnect (Exercise 6-10)</h2>
      <p><strong>Disconnect</strong> removes a service — deprovision network, stop billing, notify customer, retire assets. The logical flow often differs from Add/Modify: assetization may depend on billing only (not provision) after SMS confirmation.</p>

      <h3>Disconnect Logical Flow</h3>
      <div class="workflow">
        <div class="workflow-step">SMS Cancel Confirm</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Billing Disconnect</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Provision Deactivate</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">SMS Cancel Sent</div><span class="workflow-arrow">→</span>
        <div class="workflow-step">Assetize Disconnect</div>
      </div>

      <h3>Configuration Tasks</h3>
      <ol>
        <li>Review MACD-1:1 disconnect diagram (subset of full logical view)</li>
        <li>Add <strong>Disconnect</strong> action to scenarios on: E2E, Provision, Billing, Assetize, SMS lanes</li>
        <li>Create Spotify disconnect-specific SMS swimlane if split from modify welcome</li>
        <li>Configure dependencies: assetization waits for billing on disconnect path</li>
        <li>Test: disconnect active Spotify subscription on account</li>
      </ol>

      <div class="note"><strong>Key difference from Add</strong> Disconnect scenarios use Action = Disconnect on Spotify RFS. Dependency graph may invert — billing before assetization without waiting for provision.</div>
''')

_s('om-macd-1tom', '''
      <h2>16. MACD with 1:M Decomposition (Exercise 6-11)</h2>
      <p><strong>Streaming TV</strong> demonstrates <strong>one-to-many</strong> decomposition: one commercial offer generates multiple FRLs — service activation plus STB shipment from region-specific warehouses (Gold/Silver/Bronze tiers → different STB products and warehouses).</p>

      <h3>Why 1:M Matters</h3>
      <ul>
        <li>Single customer order spawns parallel fulfillment in different domains (shipping vs activation)</li>
        <li>Each FRL has its own scenarios and swimlanes</li>
        <li>Change orders may produce multiple FRLs from one MACD line (Disconnect old + Add new)</li>
      </ul>

      <h3>Shipping Swimlane Conditions (Task 5)</h3>
      <p>Ship tasks use <strong>conditions</strong> on order attributes — e.g. Ship STB Silver (SoCal) fires only when:</p>
      <ul>
        <li>Subscription/tier attribute = Silver</li>
        <li>Region/warehouse attribute = SoCal</li>
      </ul>
      <p>Similar conditional tasks for Gold/NorCal, Bronze/East, etc.</p>

      <h3>The Modify &quot;Trick Question&quot;</h3>
      <p>When upgrading Bronze → Silver TV, Greg discovers <strong>no dedicated Modify swimlane is needed</strong>. IOM decomposition compares inventory vs request and emits:</p>
      <ul>
        <li>FRL 1: <strong>Disconnect</strong> Bronze TV service</li>
        <li>FRL 2: <strong>Add</strong> Silver TV service</li>
      </ul>
      <p>Orchestration then runs disconnect shipping (return label + box) and add shipping (new Silver STB) in parallel with activation changes.</p>

      <h3>Dependency Layers (Tasks 7–9)</h3>
      <ul>
        <li>E2E task dependencies (Start/End framing)</li>
        <li>Shipping-specific dependencies per warehouse/tier</li>
        <li>Disconnect-specific dependencies (reverse logistics before account cleanup)</li>
      </ul>

      <h3>Test Scenarios</h3>
      <table class="data-table">
        <thead><tr><th>Task</th><th>Action</th><th>Expected</th></tr></thead>
        <tbody>
          <tr><td>10 — Add</td><td>New Streaming TV order</td><td>Activation + ship STB swimlanes fire</td></tr>
          <tr><td>11 — Change</td><td>Bronze → Silver upgrade</td><td>Disconnect Bronze + Add Silver FRLs; return label + new STB shipments</td></tr>
          <tr><td>12 — Disconnect</td><td>Cancel service</td><td>Deprovision + return shipment + billing stop</td></tr>
        </tbody>
      </table>
''')

_s('om-cancel', '''
      <h2>17. In-Flight Order Cancellation (Exercise 6-12)</h2>
      <p>Customers cancel mid-install. <strong>In-flight cancellation</strong> stops active orchestration and optionally runs rollback plans to undo completed work — unless a task hit <strong>PONR (Point of No Return)</strong>.</p>

      <h3>OC Provision Mobile — Lab Model</h3>
      <table class="data-table">
        <thead><tr><th>Element</th><th>Detail</th></tr></thead>
        <tbody>
          <tr><td>Commercial product</td><td>Mobile Data Plan Offer</td></tr>
          <tr><td>Technical product</td><td>OC Activation RFS</td></tr>
          <tr><td>Main swimlane</td><td>OC Provision Mobile (Show Order 1)</td></tr>
          <tr><td>Manual pause task</td><td>OC Pause Provision Mobile → Technical Order Reviews queue</td></tr>
          <tr><td>Rollback swimlane</td><td>OC Rollback Provision Mobile — triggered by Rollback Plan Definition, <em>not</em> scenario</td></tr>
        </tbody>
      </table>

      <h3>Rollback Plan vs Scenario</h3>
      <p>Normal forward flow uses <strong>scenarios</strong> (product + action). <strong>Cancellation rollback</strong> uses <strong>Rollback Plan Definition</strong> field on item definitions — when cancel fires, engine executes the named rollback plan instead of forward scenarios.</p>

      <h3>Configuration (Task 2)</h3>
      <ol>
        <li>Create OC Provision Mobile plan with Start milestone, Pause manual task, provision callouts</li>
        <li>Set Rollback Plan Definition on appropriate items → OC Rollback Provision Mobile plan</li>
        <li>Configure cancel on order record</li>
      </ol>

      <h3>Testing Cancel (Task 3) &amp; PONR (Task 4)</h3>
      <ul>
        <li><strong>Task 3:</strong> Cancel while Pause task is active — rollback plan executes, forward tasks freeze/cancel</li>
        <li><strong>Task 4:</strong> Let order pass PONR milestone — cancel button disabled or cancel rejected — order must complete or manual intervention required</li>
      </ul>

      <div class="warning"><strong>PONR</strong> Mark irreversible steps (number port completed, billing activated) with PONR on item definition to protect business integrity.</div>
''')

_s('om-rollback', '''
      <h2>18. Rollback Groups &amp; Smart Freeze (Exercise 6-13)</h2>
      <p>Complex cancellations require coordinated undo across many completed tasks. <strong>Rollback groups</strong> batch reverse operations; <strong>Smart Freeze</strong> pauses in-flight work while cancel processes.</p>

      <h3>Exercise Scenario</h3>
      <p>Uses pre-built product and orchestration models with richer cancel configuration than Exercise 6-12. Tests cancel at different fulfillment stages:</p>
      <ul>
        <li><strong>Mid-way cancel (Task 3):</strong> Some tasks completed, others pending — partial rollback</li>
        <li><strong>Nearly fulfilled (Task 4):</strong> Most tasks green — extensive rollback required</li>
      </ul>

      <h3>Rollback Groups (Tasks 5–6)</h3>
      <table class="data-table">
        <thead><tr><th>Concept</th><th>Description</th></tr></thead>
        <tbody>
          <tr><td><strong>Rollback Group</strong></td><td>Named group on item definitions — items in same group undo together</td></tr>
          <tr><td><strong>Rollback Plan Definition</strong></td><td>Plan with reverse callouts (deprovision, refund, inventory return)</td></tr>
          <tr><td><strong>Order Cancel Configuration</strong></td><td>Org-level settings governing cancel behavior (Task 2 review)</td></tr>
        </tbody>
      </table>

      <h3>Smart Freeze (Task 7 — Optional)</h3>
      <p>When cancel initiated while a callout is <strong>Running</strong>, Smart Freeze pauses the task instead of allowing inconsistent state — resumes or rolls back after cancel decision finalized.</p>

      <h3>Design Guidance</h3>
      <ul>
        <li>Define rollback plans mirroring forward plans (provision → deprovision, bill → unbill)</li>
        <li>Group related reverse steps to avoid partial inconsistent customer state</li>
        <li>Test cancel at every major milestone during design — not just at end</li>
      </ul>
''')

_s('om-challenge', '''
      <h2>19. Advanced Orchestration Challenge (Exercise 6-14)</h2>
      <p>Capstone lab integrating all concepts: multi-swimlane plan with manual tasks, callouts, dependencies, fallout, and <strong>staggered integration retry policies</strong>.</p>

      <h3>Tasks Overview</h3>
      <table class="data-table">
        <thead><tr><th>Task</th><th>Focus</th></tr></thead>
        <tbody>
          <tr><td>1 (optional)</td><td>Refresh orchestration concepts</td></tr>
          <tr><td>2</td><td>Review finished orchestration plan diagram — target architecture</td></tr>
          <tr><td>3</td><td>Build out plan definitions, items, scenarios, dependencies</td></tr>
          <tr><td>4</td><td>End-to-end test order through all swimlanes</td></tr>
          <tr><td>5</td><td>Configure staggered retry policy — increasing delays between retries</td></tr>
        </tbody>
      </table>

      <h3>Staggered Retry Policy</h3>
      <p>Instead of immediate repeated callouts (which can overwhelm a failing endpoint), staggered policies wait progressively longer between attempts — e.g. 30s, 2m, 10m — improving recovery odds for transient outages while routing to fallout after max attempts.</p>

      <div class="tip"><strong>Certification mindset</strong> This exercise mirrors real project delivery: diagram first, prototype with milestones, add integrations, wire dependencies, test MACD + cancel paths, harden with retry/fallout.</div>
''')

_s('om-ref', '''
      <h2>Order Management Quick Reference</h2>

      <h3>Design-Time vs Runtime</h3>
      <table class="data-table">
        <thead><tr><th>Design-Time</th><th>Runtime</th></tr></thead>
        <tbody>
          <tr><td>Orchestration Plan Definition</td><td>Orchestration Plan (swimlane instance)</td></tr>
          <tr><td>Orchestration Item Definition</td><td>Orchestration Item (task box on plan UI)</td></tr>
          <tr><td>Decomposition Relationship</td><td>Fulfillment Request Line (FRL)</td></tr>
          <tr><td>Scenario (product + action)</td><td>Activated plan for matching FRL</td></tr>
          <tr><td>Dependency Definition</td><td>Resolved wait between item states</td></tr>
        </tbody>
      </table>

      <h3>Glossary</h3>
      <table class="data-table">
        <thead><tr><th>Term</th><th>Definition</th></tr></thead>
        <tbody>
          <tr><td>Decomposition</td><td>Commercial order line → FRLs on technical products</td></tr>
          <tr><td>FRL</td><td>Fulfillment Request Line — orchestration input after decompose</td></tr>
          <tr><td>Swimlane</td><td>One orchestration plan row = one plan definition</td></tr>
          <tr><td>Show Order</td><td>Vertical sort of swimlanes (1 = top)</td></tr>
          <tr><td>Scope</td><td>Global / Swimlane — dependency resolution boundary</td></tr>
          <tr><td>Scenario</td><td>Product + Action → triggers plan definition</td></tr>
          <tr><td>MACD</td><td>Move, Add, Change (Modify), Disconnect actions</td></tr>
          <tr><td>1:1 / 1:M</td><td>One commercial line → one vs many FRLs</td></tr>
          <tr><td>PONR</td><td>Point of No Return — blocks in-flight cancel</td></tr>
          <tr><td>Rollback Plan Definition</td><td>Plan executed on cancel (not scenario-based)</td></tr>
          <tr><td>Rollback Group</td><td>Items reversed together during cancel</td></tr>
          <tr><td>Smart Freeze</td><td>Pause running tasks during cancel processing</td></tr>
          <tr><td>Fallout Queue</td><td>Manual repair queue for failed integrations</td></tr>
          <tr><td>Item Implementation</td><td>Links Auto Task to Apex (e.g. Assetize)</td></tr>
        </tbody>
      </table>

      <h3>Item State Colors (Plan UI)</h3>
      <table class="data-table">
        <thead><tr><th>Color</th><th>State</th></tr></thead>
        <tbody>
          <tr><td>Grey</td><td>Pending — waiting on dependencies</td></tr>
          <tr><td>Blue</td><td>Ready — can be picked up / about to execute</td></tr>
          <tr><td>Green</td><td>Completed</td></tr>
          <tr><td>Red / alert colors</td><td>Failed / Fatally Failed (see org theme)</td></tr>
        </tbody>
      </table>

      <p class="note"><strong>Source:</strong> Order Orchestration EG v1.0 (3).pdf — Salesforce Industries Order Management Orchestration Exercise Guide (Spring &apos;22 / 2022).</p>
''')
